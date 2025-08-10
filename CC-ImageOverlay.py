# CC-ImageOverlay.py
import sys
import os
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QSlider, QVBoxLayout, QHBoxLayout, QCheckBox, QGridLayout, QSizePolicy,
    QStatusBar, QMessageBox, QComboBox, QFrame, QRadioButton, QTextEdit,
    QColorDialog, QButtonGroup
)
from PySide6.QtGui import QScreen, QAction, QActionGroup
from PySide6.QtCore import Qt, Slot, QPoint
# ライブラリインポート
from lib.lang_loader import lang_load, get_text, config_data, lang_data, get_available_languages
from lib.cnf_loader import cf_load, cf_change
from lib.PositionPreviewWidget import PositionPreviewWidget
from lib.theme_manager import ThemeManager
from lib.overlay_windows import ImageOverlayWindow, MemoOverlayWindow

class CCImageOverlay:
    """アプリケーションのメインクラス"""
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.theme_manager = ThemeManager(self.app)
        self.config = self._load_config()
        self.lang_data = self._initialize_language()
        self.main_window = MainWindow(self.config, self.theme_manager)

    def _load_config(self):
        """設定読み込み"""
        config = cf_load()
        config.setdefault("language", "Japanese")
        config.setdefault("theme", "system")
        return config

    def _initialize_language(self):
        """言語初期化"""
        return lang_load(self.config.get("language"))

    def run(self):
        """アプリケーション実行"""
        self.theme_manager.load_theme(self.config.get("theme"))
        self.main_window.show()
        return self.app.exec()

class MainWindow(QMainWindow):
    """メインコントロールウィンドウ"""
    def __init__(self, config, theme_manager):
        """コンストラクタ"""
        super().__init__()
        self.config = config
        self.theme_manager = theme_manager

        DEFAULT_WINDOW_X = 100; DEFAULT_WINDOW_Y = 100
        DEFAULT_WINDOW_WIDTH = 450; DEFAULT_WINDOW_HEIGHT = 480
        DEFAULT_OVERLAY_SIZE = 100; DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0; DEFAULT_OVERLAY_REL_Y = 0
        DEFAULT_TARGET_MONITOR_NAME = None; DEFAULT_LAST_IMAGE = None
        DEFAULT_THEME = "system"

        # 利用可能な言語を取得
        self.available_languages = get_available_languages()
        if not self.available_languages:
            self.available_languages = ["Japanese", "English"]  # フォールバック

        initial_x = config.get("window_x", DEFAULT_WINDOW_X)
        initial_y = config.get("window_y", DEFAULT_WINDOW_Y)
        initial_width = config.get("window_width", DEFAULT_WINDOW_WIDTH)
        initial_height = config.get("window_height", DEFAULT_WINDOW_HEIGHT)
        self.last_image_path = config.get("last_image_path", DEFAULT_LAST_IMAGE)
        self.current_size_percent = config.get("overlay_size", DEFAULT_OVERLAY_SIZE)
        self.current_alpha_percent = config.get("overlay_alpha", DEFAULT_OVERLAY_ALPHA)
        self.current_relative_x = config.get("overlay_x", DEFAULT_OVERLAY_REL_X)
        self.current_relative_y = config.get("overlay_y", DEFAULT_OVERLAY_REL_Y)
        self.target_monitor_name = config.get("target_monitor_name", DEFAULT_TARGET_MONITOR_NAME)
        self.overlay_enabled = False
        self.image_path = None

        self.setGeometry(initial_x, initial_y, initial_width, initial_height)
        self.setStatusBar(QStatusBar())
        self.screens = QApplication.screens()
        self.overlay_window = ImageOverlayWindow(self)  # クラス名を変更
        self.memo_window = MemoOverlayWindow(self)
        self.current_mode = "image"  # デフォルトは画像モード

        self._create_actions()
        self._create_menus()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._retranslate_ui()
        self._initialize_ui_state()

    def _create_actions(self):
        """アクション作成"""
        self.exit_action = QAction(self)
        self.exit_action.triggered.connect(self.close)
        self.help_action = QAction(self)
        self.help_action.triggered.connect(self._handle_help)
        self.version_action = QAction(self)
        self.version_action.triggered.connect(self._handle_version)
        self.license_action = QAction(self)
        self.license_action.triggered.connect(self._handle_license)

        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_group.triggered.connect(self._change_language)
        
        # 言語アクションを動的に作成
        current_lang = self.config.get("language")  # configから取得
        self.lang_actions = {}
        for lang_name in self.available_languages:
            action = QAction("", self, checkable=True, data=lang_name)
            if current_lang == lang_name:
                action.setChecked(True)
            self.lang_group.addAction(action)
            self.lang_actions[lang_name] = action

        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.triggered.connect(self._change_theme)
        self.theme_light_action = QAction("", self, checkable=True, data="light")
        self.theme_dark_action = QAction("", self, checkable=True, data="dark")
        self.theme_system_action = QAction("", self, checkable=True, data="system")
        
        current_theme = self.config.get("theme")  # configから取得
        if current_theme == "light": self.theme_light_action.setChecked(True)
        elif current_theme == "dark": self.theme_dark_action.setChecked(True)
        else: self.theme_system_action.setChecked(True)
        self.theme_group.addAction(self.theme_light_action)
        self.theme_group.addAction(self.theme_dark_action)
        self.theme_group.addAction(self.theme_system_action)

    def _create_menus(self):
        """メニュー作成"""
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("")
        self.info_menu = menu_bar.addMenu("")
        self.settings_menu = menu_bar.addMenu("")
        self.language_menu = self.settings_menu.addMenu("")
        self.theme_menu = self.settings_menu.addMenu("")

        self.file_menu.addAction(self.exit_action)
        self.info_menu.addAction(self.help_action)
        self.info_menu.addSeparator()
        self.info_menu.addAction(self.version_action)
        self.info_menu.addAction(self.license_action)
        # 言語メニューに動的に追加
        for lang_name in self.available_languages:
            self.language_menu.addAction(self.lang_actions[lang_name])
        self.theme_menu.addAction(self.theme_light_action)
        self.theme_menu.addAction(self.theme_dark_action)
        self.theme_menu.addAction(self.theme_system_action)

    def _create_widgets(self):
        """ウィジェット作成"""
        # モード選択
        self.mode_widget = QWidget()  # インスタンス変数として保存
        self.mode_widget.setFixedHeight(32)
        self.mode_layout = QHBoxLayout()
        self.mode_layout.setContentsMargins(4, 4, 4, 4)
        self.mode_layout.setSpacing(4)
        
        self.image_radio = QRadioButton(get_text("mode_image"))
        self.memo_radio = QRadioButton(get_text("mode_memo"))
        self.image_radio.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.image_radio)
        mode_group.addButton(self.memo_radio)
        
        self.mode_layout.addWidget(self.image_radio)
        self.mode_layout.addWidget(self.memo_radio)
        self.mode_widget.setLayout(self.mode_layout)  # ここでレイアウトを設定

        # 画像モードのウィジェット
        self.select_button = QPushButton()
        self.path_label = QLabel()
        self.path_label.setObjectName("path_label")
        self.path_label.setWordWrap(True)
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(self.overlay_enabled)
        self.monitor_label = QLabel()
        self.monitor_combo = QComboBox()
        self._populate_monitor_combo()

        # 詳細設定セクション作成
        self.detail_frame = QFrame()
        self.detail_frame.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Raised)
        self.detail_frame.setContentsMargins(2, 2, 2, 2)  # Reduce frame margins
        self.detail_button = QPushButton()
        self.detail_button.setCheckable(True)
        self.detail_button.setChecked(False)
        self.detail_frame.setVisible(False)

        # 詳細設定内のウィジェット
        self.position_preview = PositionPreviewWidget()
        self.pos_x_slider = QSlider(Qt.Orientation.Horizontal)
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_x_label = QLabel()
        
        self.pos_y_slider = QSlider(Qt.Orientation.Horizontal)
        self.pos_y_slider.setValue(self.current_relative_y)
        self.pos_y_label = QLabel()
        
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(10, 300)
        self.size_slider.setValue(self.current_size_percent)
        self.size_label = QLabel()

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(0, 100)
        self.alpha_slider.setValue(self.current_alpha_percent)
        self.alpha_label = QLabel()

        # メモモードのウィジェット
        self.memo_widgets = QWidget()
        memo_layout = QGridLayout(self.memo_widgets)
        memo_layout.setContentsMargins(4, 4, 4, 4)
        memo_layout.setSpacing(4)
        
        self.memo_edit = QTextEdit()
        self.memo_edit.setMinimumHeight(100)
        self.memo_edit.setPlaceholderText(get_text("memo_placeholder"))
        
        # フォントサイズスライダーを削除
        self.bg_color_button = QPushButton(get_text("bg_color"))
        self.text_color_button = QPushButton(get_text("text_color"))

        memo_layout.addWidget(QLabel(get_text("memo_content")), 0, 0)
        memo_layout.addWidget(self.memo_edit, 1, 0)
        self.memo_widgets.setVisible(False)

        # 詳細設定のラベルとスライダーの高さを固定
        self.pos_x_label.setFixedHeight(20)
        self.pos_y_label.setFixedHeight(20)
        self.size_label.setFixedHeight(20)
        self.pos_x_slider.setFixedHeight(20)
        self.pos_y_slider.setFixedHeight(20)
        self.size_slider.setFixedHeight(20)

        # メモエディタのサイズを固定
        self.memo_edit.setFixedHeight(120)
        self.memo_edit.setFixedWidth(300)

    def _setup_layout(self):
        """レイアウト設定"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # モード選択を追加（既存のウィジェットを使用）
        main_layout.addWidget(self.mode_widget)

        # メインコントロール
        control_layout = QGridLayout()
        control_layout.setVerticalSpacing(4)  # 縦方向の間隔を固定
        
        row = 0
        control_layout.addWidget(self.select_button, row, 0)
        control_layout.addWidget(self.path_label, row, 1, 1, 2)
        row += 1
        control_layout.addWidget(self.enable_checkbox, row, 0, 1, 3)
        row += 1
        control_layout.addWidget(self.monitor_label, row, 0)
        control_layout.addWidget(self.monitor_combo, row, 1, 1, 2)
        row += 1
        control_layout.addWidget(self.alpha_label, row, 0)
        control_layout.addWidget(self.alpha_slider, row, 1, 1, 2)
        row += 1
        control_layout.addWidget(self.position_preview, row, 0, 1, 3)
        row += 1
        control_layout.addWidget(self.detail_button, row, 0, 1, 3)

        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        main_layout.addWidget(control_widget)

        # 詳細設定レイアウト
        detail_layout = QGridLayout()
        detail_layout.setVerticalSpacing(2)  # 垂直間隔を2ピクセルに固定
        detail_layout.setContentsMargins(4, 4, 4, 4)  # マージンを4ピクセルに固定

        # スライダーとラベルの高さを固定
        for widget in [self.pos_x_label, self.pos_y_label, self.size_label,
                      self.pos_x_slider, self.pos_y_slider, self.size_slider]:
            widget.setFixedHeight(20)

        row = 0
        detail_layout.addWidget(self.pos_x_label, row, 0)
        detail_layout.addWidget(self.pos_x_slider, row, 1, 1, 2)
        row += 1
        detail_layout.addWidget(self.pos_y_label, row, 0)
        detail_layout.addWidget(self.pos_y_slider, row, 1, 1, 2)
        row += 1
        detail_layout.addWidget(self.size_label, row, 0)
        detail_layout.addWidget(self.size_slider, row, 1, 1, 2)

        # 色設定ボタンは初期状態で非表示
        self.bg_color_button.setVisible(False)
        self.text_color_button.setVisible(False)

        # モードに応じて表示/非表示を切り替えるため、詳細設定に追加
        row += 1
        detail_layout.addWidget(self.bg_color_button, row, 0)
        detail_layout.addWidget(self.text_color_button, row, 1)

        self.detail_frame.setLayout(detail_layout)
        main_layout.addWidget(self.detail_frame)

        # メモウィジェットのレイアウト
        memo_layout = QGridLayout()
        memo_layout.addWidget(QLabel(get_text("memo_content")), 0, 0)
        memo_layout.addWidget(self.memo_edit, 1, 0)
        self.memo_widgets.setLayout(memo_layout)
        self.memo_widgets.setVisible(False)  # 初期状態では非表示
        main_layout.addWidget(self.memo_widgets)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _connect_signals(self):
        """シグナル接続"""
        self.select_button.clicked.connect(self.select_image)
        self.enable_checkbox.stateChanged.connect(self.toggle_overlay)
        self.monitor_combo.currentIndexChanged.connect(self._on_monitor_selected)
        self.size_slider.valueChanged.connect(self._update_state_from_size_slider)
        self.alpha_slider.valueChanged.connect(self._update_state_from_alpha_slider)
        self.position_preview.overlayGeometryChanged.connect(self._update_controls_from_preview_geom)
        self.pos_x_slider.valueChanged.connect(self._update_position_from_sliders)
        self.pos_y_slider.valueChanged.connect(self._update_position_from_sliders)
        # 詳細ボタンの接続を追加
        self.detail_button.toggled.connect(self._toggle_detail_frame)
        self.image_radio.toggled.connect(self._on_mode_changed)
        self.memo_radio.toggled.connect(self._on_mode_changed)
        self.memo_edit.textChanged.connect(self._update_memo)
        self.bg_color_button.clicked.connect(self._select_bg_color)
        self.text_color_button.clicked.connect(self._select_text_color)

    def _toggle_detail_frame(self, checked):
        """詳細設定の表示/非表示を切り替え"""
        self.detail_frame.setVisible(checked)

    def _initialize_ui_state(self):
        """UI初期状態設定"""
        self.alpha_slider.setValue(self.current_alpha_percent)
        self.size_slider.setValue(self.current_size_percent)
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_y_slider.setValue(self.current_relative_y)
        self._update_preview_widget_info()
        self._update_slider_ranges()
        self.set_controls_enabled(False)
        self.enable_checkbox.setEnabled(False)

        is_image_loaded = False
        if self.last_image_path and os.path.exists(self.last_image_path):
            self.image_path = self.last_image_path
            self.overlay_window.set_image(self.image_path)
            if self.overlay_window.original_pixmap:
                is_image_loaded = True
            else:
                self.image_path = None
                self.last_image_path = None

        self._retranslate_ui()

        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

        if is_image_loaded:
            self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
            self.overlay_window.set_alpha(self.current_alpha_percent)
            self._update_slider_ranges()
            self._update_preview_widget_info()
            self.update_position()

    def _populate_monitor_combo(self):
        """モニターコンボボックス初期化"""
        primary_screen_name = ""
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            primary_screen_name = primary_screen.name()
        saved_monitor_name = self.target_monitor_name
        selected_index = -1
        current_selection_name = None
        self.monitor_combo.blockSignals(True)
        self.monitor_combo.clear()
        if not self.screens:
             self.monitor_combo.addItem(get_text("default_monitor"), userData=None)
             self.target_monitor_name = None
             self.monitor_combo.blockSignals(False)
             print(get_text("warning_no_screens"), file=sys.stderr)
             return
        for i, screen in enumerate(self.screens):
            screen_name = screen.name()
            screen_name_display = f"Monitor {i+1}: {screen_name} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen_name == primary_screen_name:
                screen_name_display += " (Primary)"
            self.monitor_combo.addItem(screen_name_display, userData=screen_name)
            # オリジナルの選択ロジックを維持
            if saved_monitor_name == screen_name: selected_index = i
            elif saved_monitor_name is None and screen_name == primary_screen_name: selected_index = i

        if selected_index != -1:
             self.monitor_combo.setCurrentIndex(selected_index)
             current_selection_name = self.monitor_combo.itemData(selected_index)
        elif self.monitor_combo.count() > 0:
            self.monitor_combo.setCurrentIndex(0)
            current_selection_name = self.monitor_combo.itemData(0)
        self.target_monitor_name = current_selection_name
        self.monitor_combo.blockSignals(False)

    def _get_selected_screen(self) -> QScreen | None:
        """選択中のQScreenオブジェクト取得"""
        selected_name = self.monitor_combo.currentData()
        if selected_name:
            for screen in self.screens:
                if screen.name() == selected_name: return screen
        if self.screens:
             primary = QApplication.primaryScreen()
             if primary: return primary
             if self.screens: return self.screens[0]
        return None

    def _update_slider_ranges(self):
        """位置スライダーの範囲更新"""
        screen = self._get_selected_screen()
        if not screen: return
        screen_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()
        max_x = max(0, screen_geom.width() - overlay_w)
        max_y = max(0, screen_geom.height() - overlay_h)
        self.current_relative_x = max(0, min(self.current_relative_x, max_x))
        self.current_relative_y = max(0, min(self.current_relative_y, max_y))

        self.pos_x_slider.blockSignals(True)
        self.pos_y_slider.blockSignals(True)
        self.pos_x_slider.setRange(0, max_x)
        self.pos_y_slider.setRange(0, max_y)
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_y_slider.setValue(self.current_relative_y)
        self.pos_x_slider.blockSignals(False)
        self.pos_y_slider.blockSignals(False)
        self._update_position_labels()

    def _get_current_overlay_actual_size(self) -> tuple[int, int]:
        """現在のオーバーレイ実サイズ取得"""
        if self.current_mode == "memo":
            # メモモードのデフォルトサイズを基準にスケーリング
            base_w = 300  # デフォルト幅
            base_h = 200  # デフォルト高さ
            scale = self.current_size_percent / 100.0
            return (int(base_w * scale), int(base_h * scale))
        
        # 画像モードの処理（既存のコード）
        overlay_w, overlay_h = 1, 1
        current_factor = self.current_size_percent / 100.0
        if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
            orig_w = self.overlay_window.original_pixmap.width()
            orig_h = self.overlay_window.original_pixmap.height()
            if orig_w > 0 and orig_h > 0:
                overlay_w = int(round(orig_w * current_factor))
                overlay_h = int(round(orig_h * current_factor))
        return max(1, overlay_w), max(1, overlay_h)

    def _update_preview_widget_info(self):
        """プレビューウィジェット情報を更新"""
        screen = self._get_selected_screen()
        if not screen:
            return
        
        # モニターの表示可能領域を取得
        monitor_geom = screen.availableGeometry()
        
        # 現在のモードに応じたサイズを取得
        overlay_w, overlay_h = self._get_current_overlay_actual_size()  # メソッド名を修正
        
        # プレビューウィジェットの情報を更新
        self.position_preview.setMonitorGeometry(monitor_geom.width(), monitor_geom.height())
        self.position_preview.setOverlayInfo(self.current_relative_x, self.current_relative_y, overlay_w, overlay_h)

    def _update_memo_window_size(self):
        """メモウィンドウのサイズを更新"""
        if self.current_mode == "memo":
            width, height = self._get_current_overlay_actual_size()  # メソッド名を修正
            self.memo_window.setFixedSize(width, height)

    # _update_state_from_size_sliderメソッドを修正
    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダー変更処理"""
        if self.current_size_percent == value:
            return
            
        self.current_size_percent = value
        if self.current_mode == "image":
            self.size_label.setText(get_text("size_label", value=value))
            self.overlay_window.set_size_factor(value / 100.0)
        else:  # memo mode
            self.size_label.setText(get_text("font_size_label", value=value))
            self.memo_window.set_font_size(value)
        
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position()

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダー変更処理"""
        if self.current_alpha_percent == value: return
        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        if self.current_mode == "image":
            self.overlay_window.set_alpha(value)
        else:  # memo mode
            self.memo_window.set_alpha(value)  # メモウィンドウの透明度を設定

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェット変更処理"""
        if not self.position_preview.isEnabled():
            return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()
        new_actual_h = new_actual_size.height()

        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

        # サイズ変更の処理
        if self.current_mode == "memo":
            # メモモードの場合、プレビューのサイズから新しいパーセンテージを計算
            base_w = self.memo_window.default_width
            new_percent = round((new_actual_w / base_w) * 100)
            new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
            if self.current_size_percent != new_percent:
                size_changed = True
                self.current_size_percent = new_percent
                self.size_slider.blockSignals(True)
                self.size_slider.setValue(new_percent)
                self.size_slider.blockSignals(False)
                self.size_label.setText(get_text("size_label", value=new_percent))
                # メモウィンドウのサイズを更新
                self.memo_window.set_size(new_actual_w, new_actual_h)
                self.memo_window.set_font_size(new_percent)  # フォントサイズも更新
        else:
            # 画像モードの処理（既存のコード）
            if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
                original_w = self.overlay_window.original_pixmap.width()
                if original_w > 0:
                    new_percent = round((new_actual_w / original_w) * 100)
                    new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
                    if self.current_size_percent != new_percent:
                        size_changed = True
                        self.current_size_percent = new_percent
                        self.size_slider.blockSignals(True)
                        self.size_slider.setValue(new_percent)
                        self.size_slider.blockSignals(False)
                        self.size_label.setText(get_text("size_label", value=new_percent))
                        self.overlay_window.set_size_factor(new_percent / 100.0)

        # 位置変更の処理
        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            self._update_slider_ranges()
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            self.pos_x_slider.setValue(self.current_relative_x)
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            self._update_position_labels()
            self.update_position()

        if size_changed:
            self._update_slider_ranges()

        if position_changed or size_changed:
            self._update_preview_widget_info()
            self.update_position()

    @Slot()
    def _on_monitor_selected(self):
        """モニター選択変更時処理"""
        new_monitor_name = self.monitor_combo.currentData()
        if new_monitor_name is not None and new_monitor_name != self.target_monitor_name:
             self.target_monitor_name = new_monitor_name
             self._update_slider_ranges()
             self._update_preview_widget_info()
             self.update_position()

    def _retranslate_ui(self):
        """UIテキスト再翻訳"""
        self.setWindowTitle(get_text("app_title"))
        self.file_menu.setTitle(get_text("menu_file"))
        self.exit_action.setText(get_text("action_exit"))
        self.info_menu.setTitle(get_text("menu_info"))
        self.help_action.setText(get_text("action_help"))
        self.version_action.setText(get_text("action_version"))
        self.license_action.setText(get_text("action_license"))
        self.settings_menu.setTitle(get_text("menu_settings"))
        self.language_menu.setTitle(get_text("action_language"))
        # 言語メニューアイテムの翻訳 - 言語名をそのまま表示
        for lang_name, action in self.lang_actions.items():
            action.setText(lang_name)
        self.theme_menu.setTitle(get_text("action_theme"))
        for action in self.theme_group.actions():
            theme_name = action.data()
            if theme_name == "light": action.setText(get_text("theme_light"))
            elif theme_name == "dark": action.setText(get_text("theme_dark"))
            elif theme_name == "system": action.setText(get_text("theme_system"))

        self.select_button.setText(get_text("select_image_button"))
        if self.image_path:
            self.path_label.setText(os.path.basename(self.image_path))
        else:
            self.path_label.setText(get_text("no_image_selected"))
        self.enable_checkbox.setText(get_text("enable_overlay_checkbox"))
        self.monitor_label.setText(get_text("monitor_label"))
        self.size_label.setText(get_text("size_label", value=self.current_size_percent))
        self.alpha_label.setText(get_text("alpha_label", value=self.current_alpha_percent))
        # 詳細ボタンのテキスト設定を追加
        self.detail_button.setText(get_text("detail_settings_button"))
        self._update_position_labels()

    @Slot()
    def _handle_help(self):
        """ヘルプメニュー処理"""
        url = get_text("help_url")
        if url and url.startswith("http"):
             try:
                 webbrowser.open(url)
             except Exception as e:
                 # --- エラーメッセージ修正 ---
                 # 言語ファイルからタイトルとテキストを取得 (キーは仮定)
                 title = get_text("error_dialog_title", default="Error") # デフォルト値追加
                 text = get_text("error_opening_url_text", url=url, error=e, default=f"Could not open help URL: {e}") # デフォルト値追加
                 QMessageBox.warning(self, title, text)
                 # --- エラーメッセージ修正 ここまで ---
        else:
             # タイトルも言語ファイルから取得 (キーは仮定)
             title = get_text("info_dialog_title", default="Information") # デフォルト値追加
             text = get_text("info_help_url_not_configured", default="Help URL is not configured.") # デフォルト値追加
             QMessageBox.information(self, title, text)

    @Slot()
    def _handle_version(self):
        """バージョン情報メニュー処理"""
        title = get_text("version_title")
        text = get_text("version_text")
        QMessageBox.information(self, title, text)

    @Slot()
    def _handle_license(self):
        """ライセンスメニュー処理"""
        title = get_text("license_title")
        text = get_text("license_text")
        QMessageBox.information(self, title, text)

    @Slot(QAction)
    def _change_language(self, action):
        """言語変更処理"""
        new_lang = action.data()
        current_lang = self.config.get("language")  # configから取得
        if new_lang and new_lang != current_lang:
            cf_change("language", new_lang)
            self.config["language"] = new_lang  # configを更新
            lang_data = lang_load(new_lang)
            if lang_data is None:
                lang_data = {}
                print(get_text("error_lang_load_failed", lang=new_lang), file=sys.stderr)
            self._retranslate_ui()
            self._populate_monitor_combo()
            # 言語変更メッセージ表示
            title = get_text("language_change_title")
            text = get_text("language_change_text")
            QMessageBox.information(self, title, text)

    @Slot(QAction)
    def _change_theme(self, action):
        """テーマ変更処理"""
        new_theme = action.data()
        current_theme = self.config.get("theme")  # configから取得
        if new_theme and new_theme != current_theme:
            self.config["theme"] = new_theme  # configを更新
            cf_change("theme", new_theme)
            self.theme_manager.load_theme(new_theme)  # theme_managerを使用

    def set_controls_enabled(self, enabled):
        """画像依存コントロール有効/無効化"""
        self.size_slider.setEnabled(enabled)
        self.alpha_slider.setEnabled(enabled)
        self.position_preview.setEnabled(enabled)
        self.pos_x_slider.setEnabled(enabled)
        self.pos_y_slider.setEnabled(enabled)
        self.monitor_combo.setEnabled(len(self.screens) > 0)

    @Slot()
    def select_image(self):
        """画像選択処理"""
        start_dir = os.path.dirname(self.image_path) if self.image_path else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, get_text("select_image_dialog_title"), start_dir, get_text("image_files_filter")
        )
        if file_path:
            self.image_path = file_path
            self.last_image_path = file_path
            self.overlay_window.set_image(self.image_path)

            is_image_loaded = self.overlay_window.original_pixmap is not None

            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)

            if is_image_loaded:
                # 設定適用 -> 表示更新 -> スライダー/プレビュー更新 -> 位置更新
                self._update_state_from_size_slider(self.current_size_percent)
                self._update_state_from_alpha_slider(self.current_alpha_percent)
                # 画像更新を強制
                self.overlay_window.update_display()  # 追加: 画像の表示を更新
                # update_position は上記処理内で呼ばれる

                # チェックボックス状態に合わせて表示
                if self.overlay_enabled:
                    self.overlay_window.show()
                else:
                    self.overlay_window.hide()
            else:
                 self.overlay_window.hide()
                 self.image_path = None
                 self.last_image_path = None

            self._retranslate_ui() # ラベル更新

    @Slot(int)
    def toggle_overlay(self, state):
        """表示チェックボックス状態変更処理 (修正版)"""
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        
        if self.overlay_enabled:
            if self.current_mode == "image":
                if self.image_path and self.overlay_window.original_pixmap:
                    self.memo_window.hide()
                    self.overlay_window.show()
            else:  # memo mode
                self.overlay_window.hide()
                self.memo_window.show()
        else:
            self.overlay_window.hide()
            self.memo_window.hide()

    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダー変更処理"""
        if self.current_size_percent == value:
            return
            
        self.current_size_percent = value
        if self.current_mode == "image":
            self.size_label.setText(get_text("size_label", value=value))
            self.overlay_window.set_size_factor(value / 100.0)
        else:  # memo mode
            self.size_label.setText(get_text("font_size_label", value=value))
            self.memo_window.set_font_size(value)
        
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position()

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダー変更処理"""
        if self.current_alpha_percent == value: return
        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        if self.current_mode == "image":
            self.overlay_window.set_alpha(value)
        else:  # memo mode
            self.memo_window.set_alpha(value)  # メモウィンドウの透明度を設定

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェット変更処理"""
        if not self.position_preview.isEnabled():
            return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()
        new_actual_h = new_actual_size.height()

        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

        # サイズ変更の処理
        if self.current_mode == "memo":
            # メモモードの場合、プレビューのサイズから新しいパーセンテージを計算
            base_w = self.memo_window.default_width
            new_percent = round((new_actual_w / base_w) * 100)
            new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
            if self.current_size_percent != new_percent:
                size_changed = True
                self.current_size_percent = new_percent
                self.size_slider.blockSignals(True)
                self.size_slider.setValue(new_percent)
                self.size_slider.blockSignals(False)
                self.size_label.setText(get_text("size_label", value=new_percent))
                # メモウィンドウのサイズを更新
                self.memo_window.set_size(new_actual_w, new_actual_h)
                self.memo_window.set_font_size(new_percent)  # フォントサイズも更新
        else:
            # 画像モードの処理（既存のコード）
            if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
                original_w = self.overlay_window.original_pixmap.width()
                if original_w > 0:
                    new_percent = round((new_actual_w / original_w) * 100)
                    new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
                    if self.current_size_percent != new_percent:
                        size_changed = True
                        self.current_size_percent = new_percent
                        self.size_slider.blockSignals(True)
                        self.size_slider.setValue(new_percent)
                        self.size_slider.blockSignals(False)
                        self.size_label.setText(get_text("size_label", value=new_percent))
                        self.overlay_window.set_size_factor(new_percent / 100.0)

        # 位置変更の処理
        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            self._update_slider_ranges()
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            self.pos_x_slider.setValue(self.current_relative_x)
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            self._update_position_labels()
            self.update_position()

        if size_changed:
            self._update_slider_ranges()

        if position_changed or size_changed:
            self._update_preview_widget_info()
            self.update_position()

    @Slot()
    def _update_position_from_sliders(self):
        """位置スライダー変更処理"""
        new_rel_x = self.pos_x_slider.value()
        new_rel_y = self.pos_y_slider.value()

        if self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            self._update_position_labels()
            self._update_preview_widget_info()
            self.update_position()

    @Slot(bool)
    def _on_mode_changed(self, checked):
        """モード切り替え時の処理"""
        if not checked:
            return
        
        is_image_mode = self.image_radio.isChecked()
        self.current_mode = "image" if is_image_mode else "memo"
        
        # サイズスライダーの値を保存
        self._save_current_size()
        
        # ウィジェットの表示状態を更新
        self._update_mode_widgets(is_image_mode)
        # オーバーレイウィンドウの表示状態を更新
        self._update_overlay_visibility()
        
        # モードに応じたサイズを復元
        self._restore_saved_size()

    def _save_current_size(self):
        """現在のサイズを保存"""
        if not hasattr(self, '_last_mode'):
            self._last_mode = "image"
            self._saved_image_size = 100
            self._saved_memo_size = 12
            return
            
        if self._last_mode != self.current_mode:
            if self._last_mode == "image":
                self._saved_image_size = self.current_size_percent
            else:
                self._saved_memo_size = self.current_size_percent

    def _restore_saved_size(self):
        """保存されたサイズを復元"""
        if not hasattr(self, '_saved_image_size'):
            self._saved_image_size = 100
        if not hasattr(self, '_saved_memo_size'):
            self._saved_memo_size = 12

        # モードに応じたサイズを設定
        self.current_size_percent = (
            self._saved_image_size if self.current_mode == "image" 
            else self._saved_memo_size
        )
        
        # サイズスライダーを更新
        self.size_slider.setValue(self.current_size_percent)
        
        # モードに応じたラベルを更新
        label_text = (
            get_text("size_label", value=self.current_size_percent)
            if self.current_mode == "image"
            else get_text("font_size_label", value=self.current_size_percent)
        )
        self.size_label.setText(label_text)
        
        # モード変更を記録
        self._last_mode = self.current_mode

    def _update_mode_widgets(self, is_image_mode):
        """モードに応じたウィジェット表示状態を更新"""
        self.select_button.setVisible(is_image_mode)
        self.path_label.setVisible(is_image_mode)
        self.memo_widgets.setVisible(not is_image_mode)
        self.bg_color_button.setVisible(not is_image_mode)
        self.text_color_button.setVisible(not is_image_mode)
        
        # サイズスライダーのラベルを更新
        if is_image_mode:
            self.size_label.setText(get_text("size_label", value=self.current_size_percent))
        else:
            self.size_label.setText(get_text("font_size_label", value=self.current_size_percent))

    def _update_overlay_visibility(self):
        """オーバーレイウィンドウの表示状態を更新"""
        if not self.overlay_enabled:
            self.overlay_window.hide()
            self.memo_window.hide()
            return

        if self.current_mode == "image":
            self.memo_window.hide()
            if self.image_path and self.overlay_window.original_pixmap:
                self.overlay_window.show()
                self._update_overlay_window()
        else:
            self.overlay_window.hide()
            self.memo_window.show()
            self._update_memo_window()

    def _update_overlay_window(self):
        """画像オーバーレイウィンドウの状態を更新"""
        self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
        self.overlay_window.set_alpha(self.current_alpha_percent)
        self._update_window_position(self.overlay_window)

    def _update_memo_window(self):
        """メモオーバーレイウィンドウの状態を更新"""
        width, height = self._get_current_overlay_actual_size()
        self.memo_window.set_size(width, height)
        self.memo_window.set_alpha(self.current_alpha_percent)
        
        # フォントサイズを更新
        font_size = max(8, min(72, int(self.current_size_percent / 2)))  # サイズを適切な範囲に調整
        self.memo_window.set_font_size(font_size)
        
        # テキストを更新（ウィンドウサイズに合わせて調整される）
        self.memo_window.set_text(self.memo_edit.toPlainText())
        
        self._update_window_position(self.memo_window)

    def _update_window_position(self, window):
        """ウィンドウ位置を更新"""
        screen = self._get_selected_screen()
        if screen:
            screen_geom = screen.availableGeometry()
            absolute_x = screen_geom.x() + self.current_relative_x
            absolute_y = screen_geom.y() + self.current_relative_y
            if isinstance(window, ImageOverlayWindow):
                window.set_overlay_position(absolute_x, absolute_y)  # ImageOverlayWindow用
            else:
                window.set_position(absolute_x, absolute_y)  # MemoOverlayWindow用

    # 既存のupdateメソッドを置き換え
    def update_position(self):
        """全てのオーバーレイウィンドウの位置を更新"""
        if self.current_mode == "image":
            if self.overlay_window.isVisible():
                self._update_window_position(self.overlay_window)
        else:
            if self.memo_window.isVisible():
                self._update_window_position(self.memo_window)
        self._update_preview_widget_info()

    def _update_position_labels(self):
        """位置ラベルを更新"""
        self.pos_x_label.setText(get_text("pos_x_label", value=self.current_relative_x))
        self.pos_y_label.setText(get_text("pos_y_label", value=self.current_relative_y))

    def closeEvent(self, event):
        """ウィンドウクローズイベント"""
        try:
            cf_change("window_x", self.pos().x())
            cf_change("window_y", self.pos().y())
            cf_change("window_width", self.size().width())
            cf_change("window_height", self.size().height())
            cf_change("overlay_size", self.current_size_percent)
            cf_change("overlay_alpha", self.current_alpha_percent)
            cf_change("overlay_x", self.current_relative_x)
            cf_change("overlay_y", self.current_relative_y)
            cf_change("target_monitor_name", self.target_monitor_name if self.target_monitor_name is not None else "")
            if self.image_path and os.path.exists(self.image_path):
                cf_change("last_image_path", self.image_path)
            else:
                cf_change("last_image_path", "")

            # themeとlanguageの保存時に変数参照エラーが発生しないように修正
            cf_change("theme", self.config.get("theme", "system"))
            cf_change("language", self.config.get("language", "Japanese"))
        except Exception as e:
            print(f"Error saving settings: {e}", file=sys.stderr)
        
        self.overlay_window.close()
        self.memo_window.close()  # メモウィンドウも閉じる
        event.accept()

    def _update_memo(self):
        """メモテキスト更新処理"""
        if self.current_mode == "memo":
            self.memo_window.setText(self.memo_edit.toPlainText())

    def _select_bg_color(self):
        """背景色選択処理"""
        color = QColorDialog.getColor(initial=self.memo_window.get_bg_color(), parent=self)
        if color.isValid():
            self.memo_window.set_colors(color, self.memo_window.get_text_color())

    def _select_text_color(self):
        """テキスト色選択処理"""
        color = QColorDialog.getColor(initial=self.memo_window.get_text_color(), parent=self)
        if color.isValid():
            self.memo_window.set_colors(self.memo_window.get_bg_color(), color)
# --- アプリケーション実行 ---
if __name__ == "__main__":
    app = CCImageOverlay()
    sys.exit(app.run())