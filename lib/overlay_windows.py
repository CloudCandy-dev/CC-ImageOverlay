from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtWidgets import QSizePolicy
from .overlay_base import OverlayBase
import os
from .lang_loader import get_text

class ImageOverlayWindow(OverlayBase):
    """画像表示用オーバーレイ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.current_pixmap = None
        self.size_factor = 1.0
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowTransparentForInput)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_image(self, image_path: str):
        """画像を読み込む"""
        if image_path and os.path.exists(image_path):
            self.original_pixmap = QPixmap(image_path)
            if self.original_pixmap.isNull():
                if self.main_window:
                    status_text = get_text("error_loading_image_failed", image_path=os.path.basename(image_path))
                    self.main_window.statusBar().showMessage(status_text, 5000)
                self.original_pixmap = None
                self.clear()
            else:
                if self.main_window:
                    status_text = get_text("status_image_loaded", filename=os.path.basename(image_path))
                    self.main_window.statusBar().showMessage(status_text, 3000)
        else:
            self.original_pixmap = None
            self.clear()

    def set_size_factor(self, factor: float):
        """サイズ係数を設定"""
        self.size_factor = max(0.01, factor)
        self.update_display()

    def update_display(self):
        """表示を更新"""
        if not self.original_pixmap:
            self.clear()
            self.hide()
            return

        try:
            orig_w = self.original_pixmap.width()
            orig_h = self.original_pixmap.height()
            scaled_width = max(1, int(round(orig_w * self.size_factor)))
            scaled_height = max(1, int(round(orig_h * self.size_factor)))
            new_size = QSize(scaled_width, scaled_height)

            if self.current_pixmap is None or self.current_pixmap.size() != new_size:
                self.current_pixmap = self.original_pixmap.scaled(
                    new_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(self.current_pixmap)

            self.setFixedSize(new_size)
            self.setWindowOpacity(self.alpha_level)
        except Exception as e:
            if self.main_window:
                error_message = get_text("error_display_update", error=str(e))
                self.main_window.statusBar().showMessage(error_message, 5000)

    def set_overlay_position(self, x: int, y: int):
        """オーバーレイ位置設定"""
        self.move(x, y)


class MemoOverlayWindow(OverlayBase):
    """メモ表示用オーバーレイ"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text = ""
        self.font_size = 12
        self.default_width = 300
        self.default_height = 200
        self.bg_color = QColor(255, 255, 255, 200)  # 半透明の白
        self.text_color = QColor(0, 0, 0, 255)      # 不透明の黒
        
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setWordWrap(True)  # 文字の折り返しを有効化
        self.setFixedSize(self.default_width, self.default_height)

    def set_size(self, width: int, height: int):
        """サイズを設定"""
        self.setFixedSize(width, height)
        self.update_display()

    def set_text(self, text: str):
        """テキストを設定"""
        self.text = text
        self.update_display()

    def update_display(self):
        """表示を更新"""
        fm = self.fontMetrics()
        rect = QRect(0, 0, self.width() - 10, self.height() - 10)  # マージンを確保
        text = fm.elidedText(self.text, Qt.TextElideMode.ElideRight, rect.width())
        self.setText(text)
        self.update()

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
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        super().setText(self.text)
        self.update()

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
