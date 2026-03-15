# 中文词云生成器

这个目录提供一份可直接运行的 Python 脚本，用于读取中文文本、统计词频并生成词云图片。

## 功能

- 读取 `sample_text.txt` 中的中文内容
- 默认按“整句”作为词云单元生成图片
- 也支持切换为 `jieba` 分词模式
- 使用 `matplotlib` 的 `tab20` 调色板随机着色
- 白色背景、正方形布局、较紧密排版，竖排同时支持顺时针和逆时针两种方向
- 自动优先使用思源黑体，找不到时回退到系统中文字体
- 提供 Linux 桌面 GUI 版本，支持双击启动和图片预览

## 目录结构

- [generate_chinese_wordcloud.py](/home/akali/codex/word-cloud/generate_chinese_wordcloud.py)：主脚本
- [word_cloud_gui.py](/home/akali/codex/word-cloud/word_cloud_gui.py)：Linux GUI 入口
- [sample_text.txt](/home/akali/codex/word-cloud/sample_text.txt)：输入文本
- [word_cloud_output.png](/home/akali/codex/word-cloud/word_cloud_output.png)：最新生成结果
- [word_cloud_demo.png](/home/akali/codex/word-cloud/word_cloud_demo.png)：参考图片

## 安装依赖

```bash
pip install jieba matplotlib wordcloud
```

如果你要打包 Linux GUI 可执行程序，请安装：

```bash
pip install -r requirements-build.txt
```

## 运行方式

在当前目录下执行：

```bash
python3 generate_chinese_wordcloud.py
```

也可以使用绝对路径执行：

```bash
python3 /home/akali/codex/word-cloud/generate_chinese_wordcloud.py
```

运行后会生成：

```text
/home/akali/codex/word-cloud/word_cloud_output.png
```

也支持命令行参数：

```bash
python3 generate_chinese_wordcloud.py --input sample_text.txt --output output.png --unit sentence
```

## Linux GUI 运行

如果本机已安装 `PySide6`，可以直接启动 GUI：

```bash
python3 word_cloud_gui.py
```

GUI 支持：

- 直接粘贴或编辑文本
- 加载 `.txt` 文件
- 选择输出图片路径
- 切换“按句”或“分词”模式
- 生成后即时预览图片

## 输入文本

脚本默认读取 [sample_text.txt](/home/akali/codex/word-cloud/sample_text.txt)。

建议一行写一句，例如：

```text
今天的天气很好。
我正在学习编程。
终端操作很方便。
```

当前脚本会把每一句完整文本作为一个词云单元，这样不会主要拆成两个字。

## 配置说明

主要配置位于 [generate_chinese_wordcloud.py](/home/akali/codex/word-cloud/generate_chinese_wordcloud.py) 顶部：

- `FONT_PATH`：本地字体路径，默认是 `SourceHanSansSC-Regular.otf`
- `INPUT_TEXT_PATH`：输入文本文件
- `OUTPUT_IMAGE_PATH`：输出图片文件
- `TOKEN_UNIT`：词云单元模式，默认是 `"sentence"`

## 切换为分词模式

如果你想恢复为 `jieba` 分词，而不是整句模式，将：

```python
TOKEN_UNIT = "sentence"
```

改为：

```python
TOKEN_UNIT = "word"
```

这时脚本会：

- 使用 `jieba.lcut()` 进行中文分词
- 过滤停用词
- 统计词频后生成词云

## 字体说明

为了避免中文乱码，脚本会按下面顺序找字体：

1. 当前目录下匹配 `SourceHanSans*.otf` 的思源黑体文件
2. 系统中的 `NotoSansCJK-Regular.ttc`（可视为思源黑体/Noto Sans CJK）
3. 其他可用中文字体回退项

如果你的机器没有可用中文字体，请手动修改 `FONT_PATH` 为本机实际的思源黑体字体文件路径。

## 当前视觉参数

- 调色板：`tab20`
- 背景：`white`
- 画布尺寸：`800 x 800`
- 横竖比例：`prefer_horizontal=0.5`
- 词间距：`margin=2`
- 单句最大占图宽高比例：`max_text_span_ratio=0.72`
- 最高频前 5 个句子字号缩放：`reduced_emphasis_scale=0.88`

## 备注

在无图形界面的终端环境中，脚本会直接保存图片文件，不依赖窗口显示。

## 打包为 Linux GUI 程序

Linux GUI 构建文件已经准备好：

- [word_cloud_gui.spec](/home/akali/codex/word-cloud/word_cloud_gui.spec)
- [build_linux_gui.sh](/home/akali/codex/word-cloud/build_linux_gui.sh)

构建命令：

```bash
chmod +x build_linux_gui.sh
./build_linux_gui.sh
```

也可以手动执行：

```bash
python3 -m pip install -r requirements-build.txt
python3 -m PyInstaller --noconfirm --clean word_cloud_gui.spec
```

构建完成后得到：

```text
dist/word-cloud-gui
```

这个产物是无控制台窗口的 GUI 程序，适合在 Linux 桌面环境中双击启动。

如果某些 Linux 发行版启动时报 Qt `xcb` 平台插件相关错误，可先安装：

```bash
sudo apt-get install libxcb-cursor0
```
