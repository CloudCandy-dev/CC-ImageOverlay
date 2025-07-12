from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt

class MemoOverlayWindow(QLabel):
    """メモを表示するためのオーバーレイウィンドウ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.text = ""
        self.font_size = 12
        self.bg_color = QColor(255, 255, 255, 200)  # 半透明の白
        self.text_color = QColor(0, 0, 0, 255)      # 不透明の黒

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # デフォルトサイズを追加
        self.default_width = 300
        self.default_height = 200
        self.setMinimumSize(self.default_width, self.default_height)

    def update_content(self, text: str, font_size: int):
        """メモ内容を更新"""
        self.text = text
        self.font_size = font_size
        self.update_display()

    def set_colors(self, bg_color: QColor, text_color: QColor):
        """色を設定"""
        self.bg_color = bg_color
        self.text_color = text_color
        self.update()

    def update_display(self):
        """表示を更新"""
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        super().setText(self.text)
        self.update()  # adjustSize()を削除し、updateに変更

    def paintEvent(self, event):
        """背景と文字を描画"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景描画
        painter.fillRect(self.rect(), self.bg_color)
        
        # テキスト描画
        painter.setPen(self.text_color)
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.text)

    def get_bg_color(self) -> QColor:
        """背景色を取得"""
        return self.bg_color

    def get_text_color(self) -> QColor:
        """文字色を取得"""
        return self.text_color

    # メソッド名をQtの規則に合わせて変更
    def setText(self, text: str):
        """メモ内容を設定"""
        self.text = text
        self.update_display()

    def set_font_size(self, size: int):
        """フォントサイズを設定"""
        self.font_size = size
        self.update_display()

    def get_size(self) -> tuple[int, int]:
        """メモウィンドウの現在のサイズを取得"""
        return self.width(), self.height()

    def set_position(self, x: int, y: int):
        """位置を設定"""
        self.move(x, y)

    def set_alpha(self, value: int):
        """透明度を設定 (0-100)"""
        opacity = max(0.0, min(1.0, value / 100.0))
        self.setWindowOpacity(opacity)
        # 背景色の透明度も同時に更新
        self.bg_color.setAlpha(int(255 * opacity))
        self.update()

    def set_size(self, width: int, height: int):
        """サイズを設定"""
        self.setFixedSize(max(50, width), max(50, height))
        self.update()
