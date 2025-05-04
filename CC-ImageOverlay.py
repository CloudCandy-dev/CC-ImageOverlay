# CC-ImageOverlay.py
import sys
import os
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QSlider, QVBoxLayout, QHBoxLayout, QCheckBox, QGridLayout, QSizePolicy,
    QStatusBar, QMessageBox, QComboBox
)
from PySide6.QtGui import QPixmap, QScreen, QAction, QActionGroup, QCursor
from PySide6.QtCore import Qt, Slot, QPoint, QSize, QRect
# --- ローカルライブラリインポート (元の形式) ---
from lib.lang_loader import lang_load, get_text, config_data, lang_data
from lib.cnf_loader import cf_load, cf_change
from lib.PositionPreviewWidget import PositionPreviewWidget

# --- グローバル アプリケーション参照 ---
app_instance = None

# --- テーマ読み込み関数 ---
def load_and_apply_theme(theme_name):
    """指定されたテーマのスタイルシートを読み込み適用する"""
    global app_instance
    if not app_instance:
        print("エラー: テーマ読み込み時に QApplication インスタンスが利用できません。", file=sys.stderr)
        return

    qss = ""
    if theme_name != "system":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        theme_dir = os.path.join(script_dir, "themes")
        qss_file = os.path.join(theme_dir, f"{theme_name}.qss")

        if os.path.exists(qss_file):
            try:
                with open(qss_file, "r", encoding="utf-8") as f:
                    qss = f.read()
            except Exception as e:
                # MainWindow 初期化完了前に呼ばれる可能性があるので get_text は使わない
                # get_text が利用可能かどうかわからないので、エラーメッセージは英語で固定
                error_title = "Theme Loading Error"
                error_text = f"Failed to load theme file '{os.path.basename(qss_file)}':\n{e}"
                active_window = QApplication.activeWindow()
                if active_window: # メッセージボックス表示を試みる
                     QMessageBox.warning(active_window, error_title, error_text)
                else: # ダメならコンソールへ
                     print(f"{error_title}\n{error_text}", file=sys.stderr)
                qss = ""
        else:
            print(f"警告: テーマファイルが見つかりません: {qss_file}", file=sys.stderr)
            qss = ""

    try:
        app_instance.setStyleSheet(qss)
    except Exception as e:
         print(f"エラー: テーマ '{theme_name}' のスタイルシート適用中にエラー: {e}", file=sys.stderr)


# --- 初期設定読み込み (元の形式) ---
config_data = cf_load() # ここでロード (lang_loaderも内部でロードするが、こちらを優先)
current_lang = config_data.get("language", "ja") # デフォルト "ja" (元のコードに合わせる)
current_theme = config_data.get("theme", "system") # デフォルト "system" (元のコードに合わせる)
lang_load(current_lang) # lang_loader内のグローバル lang_data を更新


class OverlayWindow(QLabel):
    """画像を表示するためのオーバーレイウィンドウ"""
    def __init__(self, parent=None):
        """コンストラクタ"""
        super().__init__(parent)
        self.main_window = parent
        self.original_pixmap = None
        self.current_pixmap = None
        self.size_factor = 1.0
        self.alpha_level = 1.0

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_image(self, image_path):
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

    def update_display(self):
        """表示内容を更新する"""
        if not self.original_pixmap:
            self.clear()
            self.hide()
            return
        try:
            current_factor = self.size_factor
            orig_w = self.original_pixmap.width()
            orig_h = self.original_pixmap.height()
            scaled_width = max(1, int(round(orig_w * current_factor)))
            scaled_height = max(1, int(round(orig_h * current_factor)))
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

            if self.main_window and self.main_window.overlay_enabled:
                 if not self.isVisible(): self.show()
            else:
                 if self.isVisible(): self.hide()
        except Exception as e:
             error_message = f"表示更新エラー: {e}"
             if self.main_window:
                 self.main_window.statusBar().showMessage(error_message, 5000)
             print(f"{error_message}", file=sys.stderr)

    def set_size_factor(self, factor):
        """サイズ係数設定"""
        new_factor = max(0.01, factor)
        if abs(self.size_factor - new_factor) > 1e-6:
             self.size_factor = new_factor
             self.update_display()

    def set_alpha(self, alpha_percent):
        """透明度設定"""
        new_alpha_level = max(0.0, min(1.0, alpha_percent / 100.0))
        if abs(self.alpha_level - new_alpha_level) > 1e-6:
            self.alpha_level = new_alpha_level
            self.setWindowOpacity(self.alpha_level)

    def set_overlay_position(self, x, y):
        """オーバーレイ位置設定"""
        self.move(x, y)


class MainWindow(QMainWindow):
    """メインコントロールウィンドウ"""
    def __init__(self):
        """コンストラクタ"""
        super().__init__()
        # グローバル変数 config_data を参照 (元のコードの形式)
        global config_data

        # --- 定数 ---
        # 元のコードのデフォルト値 (Window Height は 480 になっているが、元は 300?)
        # ユーザー提供のコードでは 480 になっていたのでそちらを採用
        DEFAULT_WINDOW_X = 100; DEFAULT_WINDOW_Y = 100
        DEFAULT_WINDOW_WIDTH = 450; DEFAULT_WINDOW_HEIGHT = 480
        DEFAULT_OVERLAY_SIZE = 100; DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0; DEFAULT_OVERLAY_REL_Y = 0
        # 元のコードのデフォルト値を使用
        DEFAULT_TARGET_MONITOR_NAME = None; DEFAULT_LAST_IMAGE = None
        DEFAULT_THEME = "system"

        # --- 内部状態変数 ---
        # グローバルな config_data を使用
        initial_x = config_data.get("window_x", DEFAULT_WINDOW_X)
        initial_y = config_data.get("window_y", DEFAULT_WINDOW_Y)
        initial_width = config_data.get("window_width", DEFAULT_WINDOW_WIDTH)
        initial_height = config_data.get("window_height", DEFAULT_WINDOW_HEIGHT)
        self.last_image_path = config_data.get("last_image_path", DEFAULT_LAST_IMAGE)
        self.current_size_percent = config_data.get("overlay_size", DEFAULT_OVERLAY_SIZE)
        self.current_alpha_percent = config_data.get("overlay_alpha", DEFAULT_OVERLAY_ALPHA)
        self.current_relative_x = config_data.get("overlay_x", DEFAULT_OVERLAY_REL_X)
        self.current_relative_y = config_data.get("overlay_y", DEFAULT_OVERLAY_REL_Y)
        self.target_monitor_name = config_data.get("target_monitor_name", DEFAULT_TARGET_MONITOR_NAME)
        # self.current_theme はグローバル変数 current_theme を参照 (元の形式)
        # self.current_theme = config_data.get("theme", DEFAULT_THEME) # これは不要
        # self.current_lang はグローバル変数 current_lang を参照 (元の形式)
        # self.current_lang = config_data.get("language", "ja") # これは不要
        self.overlay_enabled = False
        self.image_path = None

        # --- ウィンドウ基本設定 ---
        self.setGeometry(initial_x, initial_y, initial_width, initial_height)
        self.setStatusBar(QStatusBar())
        self.screens = QApplication.screens()

        # --- 子ウィジェット作成 ---
        self.overlay_window = OverlayWindow(self)

        # --- UI初期化プロセス ---
        self._create_actions()
        self._create_menus()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._retranslate_ui()
        self._initialize_ui_state()

    def _create_actions(self):
        """アクション作成"""
        # グローバル変数 current_lang, current_theme を参照
        global current_lang, current_theme
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
        self.lang_ja_action = QAction("", self, checkable=True, data="ja")
        if current_lang == "ja": self.lang_ja_action.setChecked(True)
        self.lang_group.addAction(self.lang_ja_action)
        self.lang_en_action = QAction("", self, checkable=True, data="en")
        if current_lang == "en": self.lang_en_action.setChecked(True)
        self.lang_group.addAction(self.lang_en_action)
        self.lang_cn_action = QAction("", self, checkable=True, data="cn")
        if current_lang == "cn": self.lang_cn_action.setChecked(True)
        self.lang_group.addAction(self.lang_cn_action)
        self.lang_kr_action = QAction("", self, checkable=True, data="kr")
        if current_lang == "kr": self.lang_kr_action.setChecked(True)
        self.lang_group.addAction(self.lang_kr_action)

        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.triggered.connect(self._change_theme)
        self.theme_light_action = QAction("", self, checkable=True, data="light")
        self.theme_dark_action = QAction("", self, checkable=True, data="dark")
        self.theme_system_action = QAction("", self, checkable=True, data="system")
        # グローバル変数 current_theme を参照
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
        self.language_menu.addAction(self.lang_ja_action)
        self.language_menu.addAction(self.lang_en_action)
        self.language_menu.addAction(self.lang_cn_action)
        self.language_menu.addAction(self.lang_kr_action)
        self.theme_menu.addAction(self.theme_light_action)
        self.theme_menu.addAction(self.theme_dark_action)
        self.theme_menu.addAction(self.theme_system_action)

    def _create_widgets(self):
        """ウィジェット作成"""
        self.select_button = QPushButton()
        self.path_label = QLabel()
        self.path_label.setObjectName("path_label")
        self.path_label.setWordWrap(True)
        self.enable_checkbox = QCheckBox()
        self.enable_checkbox.setChecked(self.overlay_enabled)
        self.monitor_label = QLabel()
        self.monitor_combo = QComboBox()
        self._populate_monitor_combo()
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

    def _setup_layout(self):
        """レイアウト設定"""
        main_layout = QVBoxLayout()
        self.control_layout_widget = QWidget()
        control_layout = QGridLayout(self.control_layout_widget)
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
        control_layout.addWidget(self.pos_x_label, row, 0)
        control_layout.addWidget(self.pos_x_slider, row, 1, 1, 2)
        row += 1
        control_layout.addWidget(self.pos_y_label, row, 0)
        control_layout.addWidget(self.pos_y_slider, row, 1, 1, 2)
        row += 1
        control_layout.addWidget(self.size_label, row, 0)
        control_layout.addWidget(self.size_slider, row, 1, 1, 2)

        main_layout.addWidget(self.control_layout_widget)
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

        # UIテキスト設定 (path_label含む)
        self._retranslate_ui()

        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

        if is_image_loaded:
            # 設定適用し、位置を確定
            self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
            self.overlay_window.set_alpha(self.current_alpha_percent)
            self._update_slider_ranges()
            self._update_preview_widget_info()
            self.update_position() # 初期位置を設定

    def _populate_monitor_combo(self):
        """モニターコンボボックス初期化"""
        primary_screen_name = ""
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            primary_screen_name = primary_screen.name()
        # target_monitor_name は self の属性
        saved_monitor_name = self.target_monitor_name
        selected_index = -1
        current_selection_name = None
        self.monitor_combo.blockSignals(True)
        self.monitor_combo.clear()
        if not self.screens:
             self.monitor_combo.addItem("Default Monitor", userData=None)
             self.target_monitor_name = None
             self.monitor_combo.blockSignals(False)
             print("警告: 利用可能なスクリーンが見つかりません。", file=sys.stderr)
             return
        for i, screen in enumerate(self.screens):
            screen_name = screen.name()
            screen_name_display = f"Monitor {i+1}: {screen_name} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen_name == primary_screen_name:
                screen_name_display += " (Primary)"
            self.monitor_combo.addItem(screen_name_display, userData=screen_name)
            # 元のコードでは None チェックがなかったため、それに合わせる
            if saved_monitor_name == screen_name: selected_index = i
            # elif saved_monitor_name is None and screen_name == primary_screen_name: selected_index = i # 元のコードでは None チェックなし
            # 元のコードでは空文字列""との比較はしていない
            elif saved_monitor_name == "" and screen_name == primary_screen_name: selected_index = i


        if selected_index != -1:
             self.monitor_combo.setCurrentIndex(selected_index)
             current_selection_name = self.monitor_combo.itemData(selected_index)
        elif self.monitor_combo.count() > 0:
            self.monitor_combo.setCurrentIndex(0)
            current_selection_name = self.monitor_combo.itemData(0)
        # self.target_monitor_name を更新
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
             # 元のコードでは最初のスクリーンを返すフォールバックがあった
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
        """プレビューウィジェット情報更新"""
        screen = self._get_selected_screen()
        if not screen: return
        monitor_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()
        self.position_preview.setMonitorGeometry(monitor_geom.width(), monitor_geom.height())
        self.position_preview.setOverlayInfo(self.current_relative_x, self.current_relative_y, overlay_w, overlay_h)

    def _update_position_labels(self):
        """位置ラベル更新"""
        self.pos_x_label.setText(get_text("pos_x_label", value=self.current_relative_x))
        self.pos_y_label.setText(get_text("pos_y_label", value=self.current_relative_y))

    @Slot()
    def _on_monitor_selected(self):
        """モニター選択変更時処理"""
        new_monitor_name = self.monitor_combo.currentData()
        # 元のコードでは None チェックがあったのでそれに合わせる
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
        for action in self.lang_group.actions():
            lang_code = action.data()
            # 元のコードの形式に合わせる
            if lang_code == "ja": action.setText(get_text("lang_ja"))
            elif lang_code == "en": action.setText(get_text("lang_en"))
            elif lang_code == "cn": action.setText(get_text("lang_cn"))
            elif lang_code == "kr": action.setText(get_text("lang_kr"))
        self.theme_menu.setTitle(get_text("action_theme"))
        for action in self.theme_group.actions():
            theme_name = action.data()
            # 元のコードの形式に合わせる
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
        self._update_position_labels()

    @Slot()
    def _handle_help(self):
        """ヘルプメニュー処理"""
        url = get_text("help_url")
        if url and url.startswith("http"):
             try: webbrowser.open(url)
             # 元のコードではエラーメッセージを翻訳していなかった
             except Exception as e: QMessageBox.warning(self, "Error", f"Could not open help URL: {e}")
        else: QMessageBox.information(self, "Help", "Help URL is not configured.")

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
        """言語変更処理 (元の形式)"""
        # グローバル変数を参照・更新
        global current_lang, lang_data
        new_lang = action.data()
        if new_lang and new_lang != current_lang:
            cf_change("language", new_lang)
            current_lang = new_lang # グローバル変数更新
            lang_data = lang_load(current_lang) # グローバル変数 lang_data 更新
            if lang_data is None: # 念のためチェック
                lang_data = {}
                # 元のコードではメッセージボックスは出さない
                print(f"エラー: 言語データ({new_lang})の読み込みに失敗しました。", file=sys.stderr)
            # self.current_lang = new_lang # MainWindow内の属性は不要（グローバルを参照）
            self._retranslate_ui()
            self._populate_monitor_combo()
            # 元のコードには言語変更メッセージボックスがあった
            title = get_text("language_change_title")
            text = get_text("language_change_text")
            QMessageBox.information(self, title, text)


    @Slot(QAction)
    def _change_theme(self, action):
        """テーマ変更処理"""
        # グローバル変数 current_theme を参照・更新
        global current_theme
        new_theme = action.data()
        if new_theme and new_theme != current_theme:
            current_theme = new_theme # グローバル変数更新
            # self.current_theme = new_theme # MainWindow内の属性は不要
            cf_change("theme", new_theme)
            load_and_apply_theme(new_theme)

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
            # self.path_label.setText(os.path.basename(file_path)) # _retranslate_ui で設定
            self.overlay_window.set_image(self.image_path)

            is_image_loaded = self.overlay_window.original_pixmap is not None

            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)

            if is_image_loaded:
                # 設定適用 -> スライダー/プレビュー更新 -> 位置更新
                self._update_state_from_size_slider(self.current_size_percent)
                self._update_state_from_alpha_slider(self.current_alpha_percent)
                # update_position は上記で呼ばれる

                # チェックボックス状態に合わせて表示
                if self.overlay_enabled:
                    self.overlay_window.show()
                else:
                    self.overlay_window.hide()
            else:
                 self.overlay_window.hide()
                 self.image_path = None
                 self.last_image_path = None

            # ラベル更新
            self._retranslate_ui()

    @Slot(int)
    def toggle_overlay(self, state):
        """表示チェックボックス状態変更処理 (修正版)"""
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        is_image_loaded = self.image_path is not None and self.overlay_window.original_pixmap is not None

        if self.overlay_enabled and is_image_loaded:
            # --- バグ修正箇所 ---
            # 不要な更新処理を削除
            # self._update_state_from_size_slider(self.current_size_percent)
            # self._update_state_from_alpha_slider(self.current_alpha_percent)
            # self.update_position()
            # --- バグ修正箇所 ここまで ---
            self.overlay_window.show() # 表示するだけ
        else:
            self.overlay_window.hide()

    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダー変更処理"""
        if self.current_size_percent == value: return
        self.current_size_percent = value
        self.size_label.setText(get_text("size_label", value=value))
        self.overlay_window.set_size_factor(value / 100.0) # 表示更新含む
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position() # 位置更新

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダー変更処理"""
        if self.current_alpha_percent == value: return
        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        self.overlay_window.set_alpha(value) # Opacityのみ更新

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェット変更処理"""
        if not self.position_preview.isEnabled(): return

        # 元のコードにはチェックがなかったので削除 (必要なら復活させる)
        # if not self.overlay_enabled or not self.image_path or not self.overlay_window.original_pixmap:
        #    self._update_preview_widget_info()
        #    return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()

        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

        # サイズ変更反映
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
                    self.overlay_window.set_size_factor(new_percent / 100.0) # 表示更新

        # 位置変更反映
        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            self._update_slider_ranges() # 範囲更新 -> 値設定 -> ラベル更新
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            self.pos_x_slider.setValue(self.current_relative_x)
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            self._update_position_labels()

        if size_changed: # サイズ変更だけでも範囲更新
             self._update_slider_ranges()

        if position_changed or size_changed: # 変更があれば同期
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
            self.update_position() # 実際の位置更新

    def update_position(self):
        """オーバーレイの絶対位置計算・移動 (バグ修正済み)"""
        # --- バグ修正箇所 ---
        # overlay_enabled や image_path のチェックを削除
        # if not self.overlay_enabled or not self.image_path or not self.overlay_window.original_pixmap:
        #     self._update_preview_widget_info()
        #     return
        # --- バグ修正箇所 ここまで ---

        screen = self._get_selected_screen()
        if not screen: return

        screen_geom = screen.availableGeometry()
        screen_offset = screen_geom.topLeft()

        absolute_x = screen_offset.x() + self.current_relative_x
        absolute_y = screen_offset.y() + self.current_relative_y

        self.overlay_window.set_overlay_position(absolute_x, absolute_y) # 位置設定

        self._update_preview_widget_info() # プレビュー更新


    def closeEvent(self, event):
        """ウィンドウクローズイベント"""
        # グローバル変数 current_theme を参照
        global current_theme
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
            cf_change("theme", current_theme) # グローバル変数を保存
            # 言語設定は _change_language で保存済み
            print("設定を保存しました。")
        except Exception as e:
             print(f"設定保存エラー: {e}", file=sys.stderr)
        self.overlay_window.close()
        event.accept()

# --- アプリケーション実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_instance = app # グローバル参照設定
    # グローバル変数 current_theme を使用 (元の形式)
    load_and_apply_theme(current_theme) # 初期テーマ適用
    main_win = MainWindow() # メインウィンドウ作成
    main_win.show()         # 表示
    sys.exit(app.exec())    # イベントループ開始