# MainWindow 詳細設計

## 1. 概要
メインウィンドウは、アプリケーションの主要なユーザーインターフェースを提供します。画像やメモの管理、オーバーレイの制御、設定の変更などの機能を提供します。

## 2. クラス定義

```python
class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    # シグナル定義
    settings_requested = Signal()          # 設定ダイアログ表示要求
    theme_changed = Signal(str)           # テーマ変更
    language_changed = Signal(str)        # 言語変更

    def __init__(self):
        super().__init__()
        self._view_model = None
        self._preview_widget = None
        self._setup_ui()

    async def initialize(self, view_model: MainWindowViewModel) -> Result[None]:
        """初期化
        Args:
            view_model: メインウィンドウのビューモデル
        Returns:
            Result[None]: 初期化結果
        """
        try:
            self._view_model = view_model
            
            # ViewModel初期化
            vm_init_result = await view_model.initialize()
            if not vm_init_result.success:
                return vm_init_result
            
            # UI初期化
            await self._setup_connections()
            window_state_result = await self._restore_window_state()
            if not window_state_result.success:
                return window_state_result
                
            return Result(success=True, data=None)
            
        except Exception as e:
            error_msg = f"メインウィンドウの初期化に失敗: {e}"
            logger.error(error_msg)
            return Result(
                success=False,
                error=error_msg,
                error_code="MAIN_WINDOW_INIT_ERROR"
            )

    def set_preview_widget(self, widget: PreviewWidget) -> None:
        """プレビューウィジェットの設定"""
        self._preview_widget = widget
        self.preview_container.layout().addWidget(widget)

    def update_texts(self) -> None:
        """テキストの更新"""
        # メニューバーのテキスト更新
        self.menubar.update_texts()
        # ツールバーのテキスト更新
        self.toolbar.update_texts()
        # その他UIコンポーネントのテキスト更新
        self._update_ui_texts()

    def closeEvent(self, event: QCloseEvent) -> None:
        """ウィンドウクローズイベント"""
        try:
            self._save_window_state()
            event.accept()
        except Exception as e:
            logger.error(f"ウィンドウ状態の保存に失敗: {e}")
            event.accept()

    def _setup_ui(self) -> None:
        """UI構築"""
        # ウィンドウ設定
        self.setWindowTitle("CC-ImageOverlay")
        self.resize(800, 600)

        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # レイアウト
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # メニューバーの作成
        self._create_menu_bar()
        
        # ツールバーの作成
        self._create_tool_bar()
        
        # プレビューコンテナの作成
        self._create_preview_container()
        
        # コントロールパネルの作成
        self._create_control_panel()

    def _create_menu_bar(self) -> None:
        """メニューバーの作成"""
        self.menubar = MenuBar()
        self.setMenuBar(self.menubar)
        
        # ファイルメニュー
        file_menu = self.menubar.addMenu("File")
        file_menu.addAction("Open Image", self._on_open_image)
        file_menu.addAction("Exit", self.close)
        
        # 設定メニュー
        settings_menu = self.menubar.addMenu("Settings")
        settings_menu.addAction("Preferences", self._on_show_settings)

    def _create_tool_bar(self) -> None:
        """ツールバーの作成"""
        self.toolbar = ToolBar()
        self.addToolBar(self.toolbar)
        
        # ツールバーアクション
        self.toolbar.add_action("Open", "open.png", self._on_open_image)
        self.toolbar.add_action("Settings", "settings.png", self._on_show_settings)
        self.toolbar.add_separator()
        self.toolbar.add_action("Toggle", "toggle.png", self._on_toggle_overlay)

    def _create_preview_container(self) -> None:
        """プレビューコンテナの作成"""
        self.preview_container = QWidget()
        layout = QVBoxLayout()
        self.preview_container.setLayout(layout)
        self.centralWidget().layout().addWidget(self.preview_container)

    def _create_control_panel(self) -> None:
        """コントロールパネルの作成"""
        panel = QWidget()
        layout = QHBoxLayout()
        panel.setLayout(layout)
        
        # オーバーレイモード選択
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Image", "Memo"])
        layout.addWidget(self.mode_combo)
        
        # 透明度スライダー
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(80)
        layout.addWidget(self.opacity_slider)
        
        self.centralWidget().layout().addWidget(panel)

    def _setup_connections(self) -> None:
        """シグナル接続"""
        if not self._view_model:
            return

        # ViewModelからのシグナル
        self._view_model.windowStateChanged.connect(self._on_window_state_changed)
        self._view_model.overlayStateChanged.connect(self._on_overlay_state_changed)
        self._view_model.errorOccurred.connect(self._show_error)

        # UIコントロールのシグナル
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)

    def _restore_window_state(self) -> None:
        """ウィンドウ状態の復元"""
        try:
            if not self._view_model:
                return

            state = self._view_model._get_window_state()
            self.setGeometry(state["geometry"])
            
            if state["maximized"]:
                self.showMaximized()

        except Exception as e:
            logger.error(f"ウィンドウ状態の復元に失敗: {e}")

    def _save_window_state(self) -> None:
        """ウィンドウ状態の保存"""
        if not self._view_model:
            return

        geometry = self.geometry()
        self._view_model.set_window_geometry(geometry)

    def _on_open_image(self) -> None:
        """画像を開く"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image",
                "",
                "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
            )
            
            if file_path and self._view_model:
                self._view_model.load_image(file_path)

        except Exception as e:
            logger.error(f"画像を開く処理に失敗: {e}")
            self._show_error("画像を開けませんでした。")

    def _on_show_settings(self) -> None:
        """設定ダイアログを表示"""
        self.settings_requested.emit()

    def _on_toggle_overlay(self) -> None:
        """オーバーレイの表示/非表示切り替え"""
        if self._view_model:
            self._view_model.toggle_overlay()

    def _on_mode_changed(self, mode_text: str) -> None:
        """モード変更"""
        if not self._view_model:
            return

        mode = OverlayMode.IMAGE if mode_text == "Image" else OverlayMode.MEMO
        self._view_model.set_overlay_mode(mode)

    def _on_opacity_changed(self, value: int) -> None:
        """透明度変更"""
        if self._view_model:
            opacity = value / 100.0
            self._view_model.set_opacity(opacity)

    def _show_error(self, message: str) -> None:
        """エラーダイアログ表示"""
        QMessageBox.critical(self, "Error", message)

    def _update_ui_texts(self) -> None:
        """UI要素のテキスト更新"""
        # メニューアイテムのテキスト更新
        self.menubar.findChild(QMenu, "file_menu").setTitle("File")
        self.menubar.findChild(QMenu, "settings_menu").setTitle("Settings")
        
        # ツールバーアイテムのテキスト更新
        for action in self.toolbar.actions():
            if action.objectName() == "open_action":
                action.setText("Open")
            elif action.objectName() == "settings_action":
                action.setText("Settings")
            elif action.objectName() == "toggle_action":
                action.setText("Toggle Overlay")
```

## 3. レイアウト構造

### 3.1 メインレイアウト
```
MainWindow
└── CentralWidget (QWidget)
    └── MainLayout (QVBoxLayout)
        ├── MenuBar
        ├── ToolBar
        ├── PreviewContainer (QWidget)
        │   └── PreviewWidget
        └── ControlPanel (QWidget)
            ├── ModeComboBox
            └── OpacitySlider
```

### 3.2 メニュー構造
```
MenuBar
├── File
│   ├── Open Image
│   └── Exit
└── Settings
    └── Preferences
```

## 4. 主要機能

### 4.1 UI構築処理
- メニューバーの構築
- ツールバーの構築
- プレビューコンテナの構築
- コントロールパネルの構築

### 4.2 イベント処理
- ウィンドウ状態管理
- 画像ファイル選択
- オーバーレイ制御
- モード切り替え
- 透明度調整

### 4.3 多言語対応
- メニューテキストの更新
- ツールバーテキストの更新
- ダイアログテキストの更新
- エラーメッセージの更新

## 5. 状態管理

### 5.1 保存項目
- ウィンドウジオメトリ
- 最大化状態
- 選択モード
- 透明度設定
- 最後に使用した画像パス

### 5.2 状態同期
- ViewModelとの双方向バインディング
- 設定の自動保存
- 状態復元処理
- エラー時の回復処理

## 6. エラー処理

### 6.1 エラーカテゴリ
- 初期化エラー
- ファイル操作エラー
- 状態管理エラー
- UI更新エラー

### 6.2 エラーハンドリング
- エラーダイアログ表示
- ログ出力
- 状態回復
- デフォルト値の使用

## 7. リソース管理

### 7.1 画像リソース
- ツールバーアイコン
- ステータスアイコン
- プレビュー画像
- テーマ画像

### 7.2 テキストリソース
- メニューラベル
- ツールチップ
- エラーメッセージ
- ステータステキスト
