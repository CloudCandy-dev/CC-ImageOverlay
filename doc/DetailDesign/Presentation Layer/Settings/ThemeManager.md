# ThemeManager 詳細設計

## 1. 概要
アプリケーションのテーマ（外観）を管理するビューモデルクラス。QSSスタイルシートの読み込み、適用、切り替えを担当し、UIの一貫性を保証する。

## 2. クラス定義

```python
class ThemeManager(QObject):
    """テーマ管理ビューモデル"""

    themeChanged = Signal(str)  # テーマ変更シグナル
    
    def __init__(self, config_manager: ConfigManager, theme_storage: ThemeStorage):
        super().__init__()
        self._config_manager = config_manager
        self._theme_storage = theme_storage
        self._current_theme = "light"
        self._default_theme = "light"
        self._active_stylesheet = ""
        self._widget_styles = {}
        self._custom_styles = {}

    @property
    def current_theme(self) -> str:
        """現在のテーマ名を取得"""
        return self._current_theme

    @property
    def available_themes(self) -> List[str]:
        """利用可能なテーマの一覧を取得"""
        return self._theme_storage.get_available_themes()

    def initialize(self) -> bool:
        """テーママネージャの初期化"""
        try:
            saved_theme = self._config_manager.get_value(
                "app_settings.theme", self._default_theme
            )
            return self.set_theme(saved_theme)
        except Exception as e:
            logger.error(f"テーママネージャの初期化に失敗: {e}")
            return self.set_theme(self._default_theme)

    def set_theme(self, theme_name: str) -> bool:
        """テーマの設定"""
        try:
            if theme_name not in self.available_themes:
                logger.error(f"未対応のテーマ: {theme_name}")
                return False

            if self._current_theme == theme_name:
                return True

            stylesheet = self._theme_storage.load_theme(theme_name)
            if not stylesheet:
                return False

            self._active_stylesheet = stylesheet
            self._current_theme = theme_name
            self._config_manager.set_value("app_settings.theme", theme_name)
            
            # アプリケーション全体にスタイルシートを適用
            QApplication.instance().setStyleSheet(self._get_complete_stylesheet())
            self.themeChanged.emit(theme_name)
            return True

        except Exception as e:
            logger.error(f"テーマ設定に失敗: {e}")
            return False

    def set_widget_style(self, widget_class: str, style: str) -> None:
        """特定のウィジェットクラスにスタイルを設定"""
        try:
            self._widget_styles[widget_class] = style
            self._update_application_style()
        except Exception as e:
            logger.error(f"ウィジェットスタイル設定に失敗: {e}")

    def add_custom_style(self, selector: str, style: str) -> None:
        """カスタムスタイルの追加"""
        try:
            self._custom_styles[selector] = style
            self._update_application_style()
        except Exception as e:
            logger.error(f"カスタムスタイル追加に失敗: {e}")

    def clear_custom_styles(self) -> None:
        """カスタムスタイルのクリア"""
        try:
            self._custom_styles.clear()
            self._update_application_style()
        except Exception as e:
            logger.error(f"カスタムスタイルのクリアに失敗: {e}")

    def _get_complete_stylesheet(self) -> str:
        """完全なスタイルシートの生成"""
        try:
            stylesheet = self._active_stylesheet

            # ウィジェット固有のスタイルを追加
            for widget_class, style in self._widget_styles.items():
                stylesheet += f"\n{widget_class} {{\n{style}\n}}"

            # カスタムスタイルを追加
            for selector, style in self._custom_styles.items():
                stylesheet += f"\n{selector} {{\n{style}\n}}"

            return stylesheet

        except Exception as e:
            logger.error(f"スタイルシート生成に失敗: {e}")
            return self._active_stylesheet

    def _update_application_style(self) -> None:
        """アプリケーションのスタイル更新"""
        try:
            QApplication.instance().setStyleSheet(self._get_complete_stylesheet())
        except Exception as e:
            logger.error(f"アプリケーションスタイルの更新に失敗: {e}")
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from typing import Dict, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from ..services.config_manager import ConfigManager
from ..storage.theme_storage import ThemeStorage
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 テーマ管理
1. テーマリストの取得
2. テーマの切り替え
3. スタイルシートの適用
4. 設定の永続化
5. 変更通知

### 4.2 スタイル管理
1. ベーステーマの適用
2. ウィジェット固有スタイル
3. カスタムスタイル
4. スタイル結合
5. 動的更新

### 4.3 カスタマイズ
1. ウィジェット別設定
2. セレクタ指定
3. 優先順位制御
4. 動的スタイル
5. 条件付きスタイル

## 5. スタイルシート構造

### 5.1 基本構造
```css
/* ベーステーマ */
QWidget {
    background-color: #ffffff;
    color: #000000;
}

/* ウィジェット固有 */
QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
}

/* カスタム要素 */
.custom-widget {
    padding: 5px;
    margin: 2px;
}
```

### 5.2 優先順位
1. インラインスタイル
2. カスタムスタイル
3. ウィジェット固有
4. ベーステーマ
5. デフォルト値

## 6. エラー処理

### 6.1 想定されるエラー
- テーマ読み込み失敗
- 無効なスタイル構文
- リソース不足
- 適用エラー
- 設定保存失敗

### 6.2 エラー処理方針
- 読み込み失敗 → デフォルトテーマ
- 構文エラー → スタイル無視
- リソース不足 → 最小スタイル
- 適用エラー → 部分適用
- 保存失敗 → エラーログ記録

## 7. パフォーマンス最適化

### 7.1 スタイル処理
- キャッシュの活用
- 差分更新
- バッチ処理
- 遅延読み込み
- メモリ最適化

### 7.2 更新制御
- 不要な更新抑制
- 一括更新
- 優先度制御
- リソース解放
- 状態監視

## 8. 拡張性

### 8.1 テーマ拡張
- プラグイン対応
- 動的テーマ
- カラースキーム
- カスタムプロパティ
- アニメーション

### 8.2 カスタマイズ
- ユーザー定義テーマ
- スタイル上書き
- 条件付きスタイル
- 動的プロパティ
- インタラクティブ要素
