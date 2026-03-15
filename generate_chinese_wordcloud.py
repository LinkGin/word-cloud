from __future__ import annotations

import argparse
import os
import random
import re
import sys
import tempfile
from collections import Counter
from operator import itemgetter
from pathlib import Path
from random import Random

import jieba
import numpy as np

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "word_cloud_mpl"))

import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from wordcloud import WordCloud
from wordcloud.wordcloud import IntegralOccupancyMap


IS_FROZEN = getattr(sys, "frozen", False)
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else BUNDLE_DIR

# 优先使用思源黑体，避免中文乱码。
FONT_FILENAME = "SourceHanSansSC-Regular.otf"
FALLBACK_FONT_PATHS = [
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc"),
    Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"),
    Path("/usr/share/fonts/truetype/arphic/ukai.ttc"),
]

INPUT_TEXT_FILENAME = "sample_text.txt"
OUTPUT_IMAGE_FILENAME = "word_cloud_output.png"
TOKEN_UNIT = "sentence"

SAMPLE_TEXT = """
人工智能正在快速改变软件开发的方式。程序员不仅需要掌握 Python、算法、数据分析，
也需要理解自动化工作流、机器学习、系统设计和工程协作。学习编程的过程需要持续练习、
不断调试、总结经验，并把抽象的概念转化为真实可运行的应用。对于中文文本处理来说，
分词、词频统计、可视化展示都是非常实用的基础能力。词云可以帮助我们快速发现一段文本
中的高频主题，例如编程、数据、算法、分析、系统、学习、开发、工程、自动化和应用。
"""

# 可按需补充停用词，减少低信息量词汇干扰。
STOPWORDS = {
    "的",
    "了",
    "和",
    "是",
    "在",
    "也",
    "与",
    "及",
    "对",
    "把",
    "将",
    "都",
    "并",
    "中",
    "一个",
    "我们",
    "需要",
}


if os.name != "nt" and not os.environ.get("DISPLAY"):
    matplotlib.use("Agg")


class BidirectionalVerticalWordCloud(WordCloud):
    """Allow vertical words to rotate in both directions."""

    vertical_orientations = (Image.ROTATE_90, Image.ROTATE_270)

    def __init__(
        self,
        *args,
        forced_horizontal_words: set[str] | None = None,
        reduced_emphasis_words: set[str] | None = None,
        max_text_span_ratio: float = 0.72,
        reduced_emphasis_scale: float = 0.88,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.forced_horizontal_words = forced_horizontal_words or set()
        self.reduced_emphasis_words = reduced_emphasis_words or set()
        self.max_text_span_ratio = max_text_span_ratio
        self.reduced_emphasis_scale = reduced_emphasis_scale

    def _pick_orientation(self, random_state: Random):
        if random_state.random() < self.prefer_horizontal:
            return None
        return random_state.choice(self.vertical_orientations)

    def _fits_span_limit(self, box_size: tuple[int, int, int, int], orientation, width: int, height: int) -> bool:
        text_width = box_size[2] - box_size[0]
        text_height = box_size[3] - box_size[1]
        max_width = int(width * self.max_text_span_ratio)
        max_height = int(height * self.max_text_span_ratio)
        if orientation is None:
            return text_width <= max_width
        return text_height <= max_height

    def generate_from_frequencies(self, frequencies, max_font_size=None):  # noqa: C901
        frequencies = sorted(frequencies.items(), key=itemgetter(1), reverse=True)
        if len(frequencies) <= 0:
            raise ValueError("We need at least 1 word to plot a word cloud, got 0.")
        frequencies = frequencies[:self.max_words]

        max_frequency = float(frequencies[0][1])
        frequencies = [(word, freq / max_frequency) for word, freq in frequencies]

        random_state = self.random_state if self.random_state is not None else Random()

        if self.mask is not None:
            boolean_mask = self._get_bolean_mask(self.mask)
            width = self.mask.shape[1]
            height = self.mask.shape[0]
        else:
            boolean_mask = None
            height, width = self.height, self.width
        occupancy = IntegralOccupancyMap(height, width, boolean_mask)

        img_grey = Image.new("L", (width, height))
        draw = ImageDraw.Draw(img_grey)
        img_array = np.asarray(img_grey)
        font_sizes, positions, orientations, colors = [], [], [], []

        last_freq = 1.0

        if max_font_size is None:
            max_font_size = self.max_font_size

        if max_font_size is None:
            if len(frequencies) == 1:
                font_size = self.height
            else:
                self.generate_from_frequencies(dict(frequencies[:2]), max_font_size=self.height)
                sizes = [x[1] for x in self.layout_]
                try:
                    font_size = int(2 * sizes[0] * sizes[1] / (sizes[0] + sizes[1]))
                except IndexError:
                    try:
                        font_size = sizes[0]
                    except IndexError as exc:
                        raise ValueError(
                            "Couldn't find space to draw. Either the Canvas size is too small "
                            "or too much of the image is masked out."
                        ) from exc
        else:
            font_size = max_font_size

        self.words_ = dict(frequencies)

        if self.repeat and len(frequencies) < self.max_words:
            times_extend = int(np.ceil(self.max_words / len(frequencies))) - 1
            frequencies_org = list(frequencies)
            downweight = frequencies[-1][1]
            for i in range(times_extend):
                frequencies.extend(
                    [(word, freq * downweight ** (i + 1)) for word, freq in frequencies_org]
                )

        for word, freq in frequencies:
            if freq == 0:
                continue

            rs = self.relative_scaling
            if rs != 0:
                font_size = int(round((rs * (freq / float(last_freq)) + (1 - rs)) * font_size))

            if word in self.reduced_emphasis_words:
                font_size = max(self.min_font_size, int(font_size * self.reduced_emphasis_scale))

            preferred_orientation = (
                None if word in self.forced_horizontal_words else self._pick_orientation(random_state)
            )
            orientation = preferred_orientation
            tried_other_orientation = False

            while True:
                if font_size < self.min_font_size:
                    break

                font = ImageFont.truetype(self.font_path, font_size)
                transposed_font = ImageFont.TransposedFont(font, orientation=orientation)
                box_size = draw.textbbox((0, 0), word, font=transposed_font, anchor="lt")
                if not self._fits_span_limit(box_size, orientation, width, height):
                    font_size -= self.font_step
                    continue
                result = occupancy.sample_position(
                    box_size[3] + self.margin,
                    box_size[2] + self.margin,
                    random_state,
                )
                if result is not None:
                    break

                if (
                    not tried_other_orientation
                    and preferred_orientation is None
                    and self.prefer_horizontal < 1
                ):
                    orientation = random_state.choice(self.vertical_orientations)
                    tried_other_orientation = True
                else:
                    font_size -= self.font_step
                    orientation = preferred_orientation

            if font_size < self.min_font_size:
                break

            x, y = np.array(result) + self.margin // 2
            draw.text((y, x), word, fill="white", font=transposed_font)
            positions.append((x, y))
            orientations.append(orientation)
            font_sizes.append(font_size)
            colors.append(
                self.color_func(
                    word,
                    font_size=font_size,
                    position=(x, y),
                    orientation=orientation,
                    random_state=random_state,
                    font_path=self.font_path,
                )
            )

            if self.mask is None:
                img_array = np.asarray(img_grey)
            else:
                img_array = np.asarray(img_grey) + boolean_mask
            occupancy.update(img_array, x, y)
            last_freq = freq

        self.layout_ = list(zip(frequencies, font_sizes, positions, orientations, colors))
        return self


def resolve_input_text_path(input_path: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if input_path:
        candidates.append(Path(input_path).expanduser().resolve())
    candidates.extend([APP_DIR / INPUT_TEXT_FILENAME, BUNDLE_DIR / INPUT_TEXT_FILENAME])

    for path in candidates:
        if path.exists():
            return path
    return None


def load_text(input_path: str | None = None) -> str:
    resolved_input_path = resolve_input_text_path(input_path)
    if resolved_input_path is not None:
        return resolved_input_path.read_text(encoding="utf-8")
    return SAMPLE_TEXT


def split_sentences(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    chunks = re.split(r"[\n。！？!?]+", normalized)
    return [chunk.strip(" ，、；;：:\"'()（）[]【】") for chunk in chunks if chunk.strip()]


def tokenize_and_count(text: str) -> Counter[str]:
    return tokenize_and_count_by_unit(text, TOKEN_UNIT)


def tokenize_and_count_by_unit(text: str, unit_mode: str) -> Counter[str]:
    if unit_mode == "sentence":
        return Counter(split_sentences(text))

    words = jieba.lcut(text)
    filtered_words = [
        word.strip()
        for word in words
        if word.strip()
        and len(word.strip()) > 1
        and word.strip() not in STOPWORDS
    ]
    return Counter(filtered_words)


def build_tab20_color_func():
    tab20_colors = plt.get_cmap("tab20").colors
    hex_colors = [
        "#{:02x}{:02x}{:02x}".format(
            int(r * 255), int(g * 255), int(b * 255)
        )
        for r, g, b in tab20_colors
    ]

    def color_func(*args, **kwargs) -> str:
        return random.choice(hex_colors)

    return color_func


def resolve_font_path() -> Path:
    for base_dir in (APP_DIR, BUNDLE_DIR):
        exact_match = base_dir / FONT_FILENAME
        if exact_match.exists():
            return exact_match

        local_source_han_fonts = sorted(base_dir.glob("SourceHanSans*.otf"))
        if local_source_han_fonts:
            return local_source_han_fonts[0]

    for path in FALLBACK_FONT_PATHS:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"未找到中文字体文件: {FONT_FILENAME}\n"
        "请将思源黑体字体文件放到程序同目录，或修改脚本中的字体查找逻辑。"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成中文词云图片")
    parser.add_argument("--input", help="输入文本文件路径，默认优先读取程序同目录的 sample_text.txt")
    parser.add_argument("--output", help="输出图片路径，默认写入程序同目录的 word_cloud_output.png")
    parser.add_argument("--unit", choices=("sentence", "word"), default=TOKEN_UNIT, help="词云单元模式")
    parser.add_argument("--show", action="store_true", help="生成后使用 matplotlib 显示图片")
    return parser.parse_args()


def generate_word_cloud(
    text: str,
    output_path: Path,
    unit_mode: str = TOKEN_UNIT,
    show_preview: bool = False,
) -> dict[str, object]:
    font_path = resolve_font_path()
    frequencies = tokenize_and_count_by_unit(text, unit_mode)
    if not frequencies:
        raise ValueError("分词后没有得到有效词汇，请检查输入文本内容。")

    forced_horizontal_words = {word for word, _ in frequencies.most_common(3)}
    reduced_emphasis_words = {word for word, _ in frequencies.most_common(5)}

    wordcloud = BidirectionalVerticalWordCloud(
        font_path=str(font_path),
        width=800,
        height=800,
        background_color="white",
        prefer_horizontal=0.5,
        margin=2,
        collocations=False,
        random_state=42,
        forced_horizontal_words=forced_horizontal_words,
        reduced_emphasis_words=reduced_emphasis_words,
        max_text_span_ratio=0.72,
        reduced_emphasis_scale=0.88,
    ).generate_from_frequencies(frequencies)

    wordcloud = wordcloud.recolor(color_func=build_tab20_color_func(), random_state=42)
    wordcloud.to_file(str(output_path))

    if show_preview:
        plt.figure(figsize=(8, 8))
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        if os.environ.get("DISPLAY") and "agg" not in matplotlib.get_backend().lower():
            plt.show()

    return {
        "output_path": output_path.resolve(),
        "font_path": font_path,
        "unit_mode": unit_mode,
        "frequencies": frequencies,
    }


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve() if args.output else APP_DIR / OUTPUT_IMAGE_FILENAME
    text = load_text(args.input)
    result = generate_word_cloud(text, output_path=output_path, unit_mode=args.unit, show_preview=args.show)

    print(f"词云图已保存到: {result['output_path']}")
    print(f"使用字体: {result['font_path']}")
    print(f"当前单元模式: {result['unit_mode']}")
    print("词频 Top 20:")
    for word, count in result["frequencies"].most_common(20):
        print(f"{word}: {count}")


if __name__ == "__main__":
    main()
