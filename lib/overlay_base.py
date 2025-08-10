from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter

class OverlayBase(QLabel):
    """オーバーレイウィンドウの基底クラス"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.alpha_level = 1.0
        self.pos = QPoint(0, 0)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_alpha(self, value: int):
        """透明度を設定 (0-100)"""
        self.alpha_level = max(0.0, min(1.0, value / 100.0))
        self.setWindowOpacity(self.alpha_level)

    def set_position(self, x: int, y: int):
        """位置を設定"""
        self.move(x, y)
        self.pos = QPoint(x, y)

    def get_position(self) -> QPoint:
        """現在の位置を取得"""
        return self.pos

    def update_display(self):
        """表示を更新（サブクラスで実装）"""
        raise NotImplementedError
