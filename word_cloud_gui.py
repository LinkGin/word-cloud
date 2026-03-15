from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from generate_chinese_wordcloud import APP_DIR, OUTPUT_IMAGE_FILENAME, generate_word_cloud, load_text


class WordCloudWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.current_pixmap: QPixmap | None = None
        self.output_path = APP_DIR / OUTPUT_IMAGE_FILENAME

        self.setWindowTitle("中文词云生成器")
        self.resize(1280, 860)
        self.setMinimumSize(QSize(1080, 760))

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(18)

        left_panel = self.build_left_panel()
        right_panel = self.build_right_panel()
        root_layout.addWidget(left_panel, 0)
        root_layout.addWidget(right_panel, 1)

        self.apply_styles()
        self.load_sample_text()
        self.output_edit.setText(str(self.output_path))

    def build_left_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(420)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("中文词云生成器")
        title.setObjectName("title")
        subtitle = QLabel("双击启动后即可编辑文本、选择模式并生成预览。")
        subtitle.setObjectName("subtitle")

        toolbar = QHBoxLayout()
        load_button = QPushButton("加载文本文件")
        load_button.clicked.connect(self.open_text_file)
        sample_button = QPushButton("恢复示例文本")
        sample_button.clicked.connect(self.load_sample_text)
        toolbar.addWidget(load_button)
        toolbar.addWidget(sample_button)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("在这里输入中文文本。建议一行一句。")

        unit_label = QLabel("词云单元")
        self.unit_combo = QComboBox()
        self.unit_combo.addItem("按句", "sentence")
        self.unit_combo.addItem("分词", "word")

        output_label = QLabel("输出图片")
        output_bar = QHBoxLayout()
        self.output_edit = QLineEdit()
        output_button = QPushButton("选择路径")
        output_button.clicked.connect(self.choose_output_path)
        output_bar.addWidget(self.output_edit, 1)
        output_bar.addWidget(output_button)

        action_bar = QHBoxLayout()
        self.generate_button = QPushButton("生成词云")
        self.generate_button.setObjectName("primary")
        self.generate_button.clicked.connect(self.generate_image)
        self.open_folder_button = QPushButton("打开输出文件")
        self.open_folder_button.clicked.connect(self.open_output_file)
        action_bar.addWidget(self.generate_button)
        action_bar.addWidget(self.open_folder_button)

        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(toolbar)
        layout.addWidget(self.text_edit, 1)
        layout.addWidget(unit_label)
        layout.addWidget(self.unit_combo)
        layout.addWidget(output_label)
        layout.addLayout(output_bar)
        layout.addLayout(action_bar)
        layout.addWidget(self.status_label)
        return panel

    def build_right_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        preview_title = QLabel("图片预览")
        preview_title.setObjectName("title")
        preview_note = QLabel("生成后会自动刷新。大图可滚动查看。")
        preview_note.setObjectName("subtitle")

        self.preview_label = QLabel("尚未生成图片")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setObjectName("preview")
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview_label)
        scroll.setFrameShape(QFrame.NoFrame)

        layout.addWidget(preview_title)
        layout.addWidget(preview_note)
        layout.addWidget(scroll, 1)
        return panel

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #f4f1ea;
                color: #1f2933;
                font-family: "Noto Sans CJK SC", "Source Han Sans SC", sans-serif;
                font-size: 14px;
            }
            QFrame#panel {
                background: #fffdf8;
                border: 1px solid #ded5c7;
                border-radius: 18px;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: 700;
                color: #182433;
            }
            QLabel#subtitle {
                color: #5f6b76;
            }
            QLabel#status {
                color: #264653;
                background: #edf6f3;
                border-radius: 12px;
                padding: 10px 12px;
            }
            QLabel#preview {
                background: #ffffff;
                border: 1px dashed #c8bcae;
                border-radius: 16px;
                min-height: 640px;
            }
            QPlainTextEdit, QLineEdit, QComboBox {
                background: #fffdfa;
                border: 1px solid #d8cfc2;
                border-radius: 12px;
                padding: 10px 12px;
            }
            QPushButton {
                background: #efe3cc;
                border: 1px solid #d9c29f;
                border-radius: 12px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton#primary {
                background: #d7701f;
                color: white;
                border-color: #c45d13;
            }
            QPushButton:hover {
                background: #e7d6b8;
            }
            QPushButton#primary:hover {
                background: #c96317;
            }
            """
        )

    def load_sample_text(self) -> None:
        self.text_edit.setPlainText(load_text())
        self.status_label.setText("已加载示例文本。")

    def open_text_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文本文件",
            str(APP_DIR),
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return

        try:
            text = Path(file_path).read_text(encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "读取失败", str(exc))
            return

        self.text_edit.setPlainText(text)
        self.status_label.setText(f"已加载文本文件：{file_path}")

    def choose_output_path(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出图片",
            str(self.output_path),
            "PNG Image (*.png)",
        )
        if file_path:
            if not file_path.lower().endswith(".png"):
                file_path += ".png"
            self.output_edit.setText(file_path)

    def generate_image(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "内容为空", "请输入文本或先加载文本文件。")
            return

        output_path_text = self.output_edit.text().strip()
        if not output_path_text:
            QMessageBox.warning(self, "缺少输出路径", "请先选择输出图片路径。")
            return

        output_path = Path(output_path_text).expanduser().resolve()
        unit_mode = self.unit_combo.currentData()

        try:
            result = generate_word_cloud(text, output_path=output_path, unit_mode=unit_mode)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "生成失败", str(exc))
            self.status_label.setText("生成失败，请检查输入文本、字体和输出路径。")
            return

        self.output_path = output_path
        self.refresh_preview(output_path)
        top_words = list(result["frequencies"].most_common(5))
        top_words_text = "，".join(f"{word}({count})" for word, count in top_words)
        self.status_label.setText(
            f"生成成功：{result['output_path']}\n"
            f"字体：{result['font_path']}\n"
            f"模式：{result['unit_mode']}\n"
            f"Top 5：{top_words_text}"
        )

    def refresh_preview(self, image_path: Path) -> None:
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.preview_label.setText("图片已生成，但预览加载失败。")
            self.current_pixmap = None
            return

        self.current_pixmap = pixmap
        self.update_preview_pixmap()

    def update_preview_pixmap(self) -> None:
        if self.current_pixmap is None:
            return
        scaled = self.current_pixmap.scaled(
            self.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.update_preview_pixmap()

    def open_output_file(self) -> None:
        output_path = Path(self.output_edit.text().strip()).expanduser()
        if not output_path.exists():
            QMessageBox.information(self, "文件不存在", "请先生成图片。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))


def main() -> None:
    app = QApplication(sys.argv)
    window = WordCloudWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
