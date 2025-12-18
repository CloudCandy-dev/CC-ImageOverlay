# UIManager 詳細設計

## 1. 概要
UIManagerは、アプリケーションのUIコンポーネント全体を管理し、ViewとViewModelレイヤー間の調整を行う中心的なコンポーネントです。

## 2. クラス定義

```python
class UIManager:
    """UIコンポーネント管理クラス"""

    def __init__(self, config_manager: ConfigManager,
                 language_manager: LanguageManager,
                 theme_manager: ThemeManager):
        self._config_manager = config_manager
        self._language_manager = language_manager
        self._theme_manager = theme_manager
        
        # UI Components
        self._main_window = None
        self._overlay_windows = {}
        self._preview_widget = None
        self._settings_dialog = None

    def initialize(self) -> bool:
        """UIシステムの初期化"""
        try:
            # 言語とテーマの初期化
            self._language_manager.load()
            self._theme_manager.load()
            
            # メインウィンドウの作成
            self._create_main_window()
            
            # プレビューウィジェットの初期化
            self._create_preview_widget()
            
            # 設定ダイアログの準備
            self._create_settings_dialog()
            
            return True

        except Exception as e:
            logger.error(f"UIManagerの初期化に失敗: {e}")
            return False

    def show_main_window(self) -> None:
        """メインウィンドウの表示"""
        if self._main_window:
            self._main_window.show()

    def create_overlay_window(self, overlay_id: str) -> None:
        """新規オーバーレイウィンドウの作成"""
        try:
            if overlay_id in self._overlay_windows:
                return
                
            window = OverlayWindow()
            window.initialize()
            self._overlay_windows[overlay_id] = window

        except Exception as e:
            logger.error(f"オーバーレイウィンドウの作成に失敗: {e}")

    def show_settings(self) -> None:
        """設定ダイアログの表示"""
        if self._settings_dialog:
            self._settings_dialog.show()

    def apply_theme(self, theme_name: str) -> None:
        """テーマの適用"""
        try:
            # テーマの読み込みと適用
            theme = self._theme_manager.load_theme(theme_name)
            if not theme:
                return

            # 各UIコンポーネントにテーマを適用
            if self._main_window:
                self._main_window.setStyleSheet(theme)
            
            for window in self._overlay_windows.values():
                window.setStyleSheet(theme)

            if self._settings_dialog:
                self._settings_dialog.setStyleSheet(theme)

        except Exception as e:
            logger.error(f"テーマの適用に失敗: {e}")

    def apply_language(self, language_code: str) -> None:
        """言語の適用"""
        try:
            # 言語リソースの読み込みと適用
            if not self._language_manager.change_language(language_code):
                return

            # 各UIコンポーネントのテキストを更新
            self._update_ui_texts()

        except Exception as e:
            logger.error(f"言語の適用に失敗: {e}")

    def _create_main_window(self) -> None:
        """メインウィンドウの作成"""
        self._main_window = MainWindow()
        self._main_window.initialize()
        
        # シグナル接続
        self._setup_main_window_signals()

    def _create_preview_widget(self) -> None:
        """プレビューウィジェットの作成"""
        self._preview_widget = PreviewWidget()
        self._preview_widget.initialize()
        
        if self._main_window:
            self._main_window.set_preview_widget(self._preview_widget)

    def _create_settings_dialog(self) -> None:
        """設定ダイアログの作成"""
        self._settings_dialog = SettingsDialog(
            self._config_manager,
            self._language_manager,
            self._theme_manager
        )

    def _setup_main_window_signals(self) -> None:
        """メインウィンドウのシグナル接続"""
        if not self._main_window:
            return

        self._main_window.settings_requested.connect(self.show_settings)
        self._main_window.theme_changed.connect(self.apply_theme)
        self._main_window.language_changed.connect(self.apply_language)

    def _update_ui_texts(self) -> None:
        """UI要素のテキスト更新"""
        if self._main_window:
            self._main_window.update_texts()
            
        if self._settings_dialog:
            self._settings_dialog.update_texts()
            
        for window in self._overlay_windows.values():
            window.update_texts()
```

## 3. 主要コンポーネントの説明

### 3.1 管理対象コンポーネント
- メインウィンドウ (`MainWindow`)
- オーバーレイウィンドウ群 (`OverlayWindow`)
- プレビューウィジェット (`PreviewWidget`)
- 設定ダイアログ (`SettingsDialog`)

### 3.2 依存コンポーネント
- `ConfigManager`: 設定管理
- `LanguageManager`: 言語リソース管理
- `ThemeManager`: テーマ管理

## 4. 主要機能

### 4.1 初期化フロー
1. 言語マネージャーの初期化
2. テーママネージャーの初期化
3. メインウィンドウの作成
4. プレビューウィジェットの初期化
5. 設定ダイアログの準備

### 4.2 言語切り替え処理
1. 言語リソースのロード
2. 全UIコンポーネントのテキスト更新
3. 設定の保存

### 4.3 テーマ切り替え処理
1. テーマファイルのロード
2. スタイルシートの適用
3. 設定の保存

## 5. エラー処理

### 5.1 エラーカテゴリ
- 初期化エラー
- リソースロードエラー
- UIコンポーネント作成エラー
- テーマ適用エラー
- 言語切り替えエラー

### 5.2 エラーハンドリング
- 各操作でのエラーキャッチ
- ログ出力
- エラー状態からの復帰処理

## 6. イベント管理

### 6.1 シグナル接続
- メインウィンドウイベント
- 設定ダイアログイベント
- オーバーレイウィンドウイベント

### 6.2 イベントフロー
1. UIイベント発生
2. シグナル伝播
3. 対応するハンドラー実行
4. 状態更新
5. UI更新

## 7. 設定の永続化

### 7.1 保存タイミング
- 言語切り替え時
- テーマ切り替え時
- ウィンドウ位置変更時
- その他設定変更時

### 7.2 保存データ
```json
{
    "ui_settings": {
        "language": string,
        "theme": string,
        "main_window": {
            "geometry": {
                "x": number,
                "y": number,
                "width": number,
                "height": number
            }
        }
    }
}
```
