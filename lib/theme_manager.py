import os
import sys
from PySide6.QtWidgets import QApplication, QMessageBox

from lib.lang_loader import get_text


class ThemeManager:
    """テーマ管理クラス"""

    def __init__(self, app: QApplication):
        self._app = app
        self._theme_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes")
        self._current_theme = "system"

    def load_theme(self, theme_name: str) -> bool:
        """テーマを読み込んで適用"""
        if theme_name == "system":
            self._app.setStyleSheet("")
            self._current_theme = theme_name
            return True

        theme_file = os.path.join(self._theme_dir, f"{theme_name}.qss")
        if not os.path.exists(theme_file):
            print(get_text("warning_theme_file_not_found", filename=theme_file), file=sys.stderr)
            return False

        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                self._app.setStyleSheet(f.read())
                self._current_theme = theme_name
                return True
        except Exception as e:
            active_window = self._app.activeWindow()
            error_text = get_text("theme_load_error_text", filename=os.path.basename(theme_file), error=str(e))
            if active_window:
                QMessageBox.warning(active_window, get_text("theme_load_error_title"), error_text)
            else:
                print(error_text, file=sys.stderr)
            return False

    @property
    def current_theme(self) -> str:
        """現在のテーマ名を取得"""
        return self._current_theme

    @property
    def theme_dir(self) -> str:
        """テーマディレクトリを取得"""
        return self._theme_dir
