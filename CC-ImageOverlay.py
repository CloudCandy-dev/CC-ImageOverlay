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
from lib.lang_loader import lang_load, get_text, config_data, lang_data
from lib.cnf_loader import cf_load, cf_change
from lib.PositionPreviewWidget import PositionPreviewWidget

APP_VERSION = "1.0.0"

# --- Global Application Reference ---
app_instance = None

# --- Theme Loading Function ---
def load_and_apply_theme(theme_name):
    """Load and apply the specified theme stylesheet."""
    global app_instance
    if not app_instance:
        print("Error: QApplication instance not available for theme loading.", file=sys.stderr)
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
                error_title = get_text("theme_load_error_title")
                error_text = get_text("theme_load_error_text", filename=os.path.basename(qss_file), error=e)
                if QApplication.activeWindow():
                     QMessageBox.warning(QApplication.activeWindow(), error_title, error_text)
                else:
                     print(f"{error_title}\n{error_text}", file=sys.stderr)
                qss = ""
        else:
            print(f"Warning: Theme file not found: {qss_file}", file=sys.stderr)
            qss = ""

    try:
        app_instance.setStyleSheet(qss)
    except Exception as e:
         print(f"Error applying stylesheet for theme '{theme_name}': {e}", file=sys.stderr)


# --- Initial Settings Load ---
config_data = cf_load()
current_lang = config_data.get("language", "ja")
current_theme = config_data.get("theme", "system")
lang_load(current_lang)


class OverlayWindow(QLabel):
    """画像を表示するためのオーバーレイウィンドウ"""
    def __init__(self, parent=None):
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
             error_message = f"Error updating display: {e}"
             if self.main_window:
                 self.main_window.statusBar().showMessage(error_message, 5000)
             print(f"{error_message}", file=sys.stderr)

    def set_size_factor(self, factor):
        new_factor = max(0.01, factor)
        if abs(self.size_factor - new_factor) > 1e-6:
             self.size_factor = new_factor
             self.update_display()

    def set_alpha(self, alpha_percent):
        new_alpha_level = max(0.0, min(1.0, alpha_percent / 100.0))
        if abs(self.alpha_level - new_alpha_level) > 1e-6:
            self.alpha_level = new_alpha_level
            self.setWindowOpacity(self.alpha_level)

    def set_overlay_position(self, x, y):
        self.move(x, y)


class MainWindow(QMainWindow):
    """メインコントロールウィンドウ"""
    def __init__(self):
        super().__init__()

        DEFAULT_WINDOW_X = 100; DEFAULT_WINDOW_Y = 100
        DEFAULT_WINDOW_WIDTH = 450; DEFAULT_WINDOW_HEIGHT = 480
        DEFAULT_OVERLAY_SIZE = 100; DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0; DEFAULT_OVERLAY_REL_Y = 0
        DEFAULT_TARGET_MONITOR_NAME = None; DEFAULT_LAST_IMAGE = None
        DEFAULT_THEME = "system"

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
        self.current_theme = config_data.get("theme", DEFAULT_THEME)
        self.overlay_enabled = False
        self.image_path = None

        self.setGeometry(initial_x, initial_y, initial_width, initial_height)
        self.setStatusBar(QStatusBar())
        self.screens = QApplication.screens()
        self.overlay_window = OverlayWindow(self)

        self._create_actions()
        self._create_menus()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._retranslate_ui()
        self._initialize_ui_state()

    def _create_actions(self):
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

        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_group.triggered.connect(self._change_theme)
        self.theme_light_action = QAction("", self, checkable=True, data="light")
        self.theme_dark_action = QAction("", self, checkable=True, data="dark")
        self.theme_system_action = QAction("", self, checkable=True, data="system")
        if self.current_theme == "light": self.theme_light_action.setChecked(True)
        elif self.current_theme == "dark": self.theme_dark_action.setChecked(True)
        else: self.theme_system_action.setChecked(True)
        self.theme_group.addAction(self.theme_light_action)
        self.theme_group.addAction(self.theme_dark_action)
        self.theme_group.addAction(self.theme_system_action)

    def _create_menus(self):
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
        self.theme_menu.addAction(self.theme_light_action)
        self.theme_menu.addAction(self.theme_dark_action)
        self.theme_menu.addAction(self.theme_system_action)

    def _create_widgets(self):
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
        """ウィジェットをレイアウトに配置 (修正後の順序)"""
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
        # --- 透明度 ---
        control_layout.addWidget(self.alpha_label, row, 0)
        control_layout.addWidget(self.alpha_slider, row, 1, 1, 2)
        row += 1
        # --- プレビュー ---
        control_layout.addWidget(self.position_preview, row, 0, 1, 3)
        row += 1
        # --- 位置 X ---
        control_layout.addWidget(self.pos_x_label, row, 0)
        control_layout.addWidget(self.pos_x_slider, row, 1, 1, 2)
        row += 1
        # --- 位置 Y ---
        control_layout.addWidget(self.pos_y_label, row, 0)
        control_layout.addWidget(self.pos_y_slider, row, 1, 1, 2)
        row += 1
        # --- サイズ ---
        control_layout.addWidget(self.size_label, row, 0)
        control_layout.addWidget(self.size_slider, row, 1, 1, 2)

        main_layout.addWidget(self.control_layout_widget)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.select_button.clicked.connect(self.select_image)
        self.enable_checkbox.stateChanged.connect(self.toggle_overlay)
        self.monitor_combo.currentIndexChanged.connect(self._on_monitor_selected)
        self.size_slider.valueChanged.connect(self._update_state_from_size_slider)
        self.alpha_slider.valueChanged.connect(self._update_state_from_alpha_slider)
        self.position_preview.overlayGeometryChanged.connect(self._update_controls_from_preview_geom)
        self.pos_x_slider.valueChanged.connect(self._update_position_from_sliders)
        self.pos_y_slider.valueChanged.connect(self._update_position_from_sliders)

    def _initialize_ui_state(self):
        """UIの初期状態を設定"""
        self.alpha_slider.setValue(self.current_alpha_percent)
        self.size_slider.setValue(self.current_size_percent)
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_y_slider.setValue(self.current_relative_y)
        self._update_preview_widget_info()
        self._update_slider_ranges()
        self.set_controls_enabled(False)
        self.enable_checkbox.setEnabled(False)

        if self.last_image_path and os.path.exists(self.last_image_path):
            self.image_path = self.last_image_path
            self.path_label.setText(os.path.basename(self.image_path))
            self.overlay_window.set_image(self.image_path)
            if self.overlay_window.original_pixmap:
                self.enable_checkbox.setEnabled(True)
                self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
                self.overlay_window.set_alpha(self.current_alpha_percent)
                self._update_slider_ranges()
                self._update_preview_widget_info()
                self.update_position()
            else:
                self.image_path = None
                self.last_image_path = None
                self.path_label.setText(get_text("no_image_selected"))
        else:
             self.path_label.setText(get_text("no_image_selected"))

        is_image_loaded = self.overlay_window.original_pixmap is not None
        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

    def _populate_monitor_combo(self):
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
             self.monitor_combo.addItem("Default Monitor", userData=None)
             self.target_monitor_name = None
             self.monitor_combo.blockSignals(False)
             print("Warning: No screens found.", file=sys.stderr)
             return
        for i, screen in enumerate(self.screens):
            screen_name_display = f"Monitor {i+1}: {screen.name()} ({screen.geometry().width()}x{screen.geometry().height()})"
            if screen.name() == primary_screen_name:
                screen_name_display += " (Primary)"
            self.monitor_combo.addItem(screen_name_display, userData=screen.name())
            if saved_monitor_name == screen.name(): selected_index = i
            elif saved_monitor_name is None and screen.name() == primary_screen_name: selected_index = i
        if selected_index != -1:
             self.monitor_combo.setCurrentIndex(selected_index)
             current_selection_name = self.monitor_combo.itemData(selected_index)
        elif self.monitor_combo.count() > 0:
            self.monitor_combo.setCurrentIndex(0)
            current_selection_name = self.monitor_combo.itemData(0)
        self.target_monitor_name = current_selection_name
        self.monitor_combo.blockSignals(False)

    def _get_selected_screen(self) -> QScreen | None:
        selected_name = self.monitor_combo.currentData()
        if selected_name:
            for screen in self.screens:
                if screen.name() == selected_name: return screen
        if self.screens:
             primary = QApplication.primaryScreen();
             if primary: return primary
             if self.screens: return self.screens[0]
        return None

    def _update_slider_ranges(self):
        screen = self._get_selected_screen()
        if not screen: return
        screen_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()
        max_x = max(0, screen_geom.width() - overlay_w)
        max_y = max(0, screen_geom.height() - overlay_h)
        self.current_relative_x = min(self.current_relative_x, max(0, max_x))
        self.current_relative_y = min(self.current_relative_y, max(0, max_y))
        self.pos_x_slider.blockSignals(True)
        self.pos_y_slider.blockSignals(True)
        self.pos_x_slider.setRange(0, max(0, max_x))
        self.pos_y_slider.setRange(0, max(0, max_y))
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_y_slider.setValue(self.current_relative_y)
        self.pos_x_slider.blockSignals(False)
        self.pos_y_slider.blockSignals(False)
        self._update_position_labels()

    def _get_current_overlay_actual_size(self) -> tuple[int, int]:
        overlay_w, overlay_h = 50, 50
        current_factor = self.current_size_percent / 100.0
        if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
             orig_w = self.overlay_window.original_pixmap.width()
             orig_h = self.overlay_window.original_pixmap.height()
             if orig_w > 0 and orig_h > 0:
                 overlay_w = int(round(orig_w * current_factor))
                 overlay_h = int(round(orig_h * current_factor))
        return max(1, overlay_w), max(1, overlay_h)

    def _update_preview_widget_info(self):
        screen = self._get_selected_screen()
        if not screen: return
        monitor_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()
        self.position_preview.setMonitorGeometry(monitor_geom.width(), monitor_geom.height())
        self.position_preview.setOverlayInfo(self.current_relative_x, self.current_relative_y, overlay_w, overlay_h)

    def _update_position_labels(self):
        self.pos_x_label.setText(get_text("pos_x_label", value=self.current_relative_x))
        self.pos_y_label.setText(get_text("pos_y_label", value=self.current_relative_y))

    @Slot()
    def _on_monitor_selected(self):
        new_monitor_name = self.monitor_combo.currentData()
        if new_monitor_name and new_monitor_name != self.target_monitor_name:
             self.target_monitor_name = new_monitor_name
             self._update_slider_ranges()
             self._update_preview_widget_info()
             self.update_position()

    def _retranslate_ui(self):
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
            if lang_code == "ja": action.setText(get_text("lang_ja"))
            elif lang_code == "en": action.setText(get_text("lang_en"))
        # Theme menu text update
        self.theme_menu.setTitle(get_text("action_theme"))
        for action in self.theme_group.actions():
            theme_name = action.data()
            if theme_name == "light": action.setText(get_text("theme_light"))
            elif theme_name == "dark": action.setText(get_text("theme_dark"))
            elif theme_name == "system": action.setText(get_text("theme_system"))

        self.select_button.setText(get_text("select_image_button"))
        if not self.image_path: self.path_label.setText(get_text("no_image_selected"))
        self.enable_checkbox.setText(get_text("enable_overlay_checkbox"))
        self.monitor_label.setText(get_text("monitor_label"))
        self.size_label.setText(get_text("size_label", value=self.current_size_percent))
        self.alpha_label.setText(get_text("alpha_label", value=self.current_alpha_percent))
        self._update_position_labels()

    @Slot()
    def _handle_help(self):
        url = get_text("help_url")
        if url and url.startswith("http"):
             try: webbrowser.open(url)
             except Exception as e: QMessageBox.warning(self, "Error", f"Could not open help URL: {e}")
        else: QMessageBox.information(self, "Help", "Help URL is not configured.")

    @Slot()
    def _handle_version(self):
        title = get_text("version_title")
        text = get_text("version_text").replace("1.0.0", APP_VERSION)
        QMessageBox.information(self, title, text)

    @Slot()
    def _handle_license(self):
        title = get_text("license_title")
        text = get_text("license_text")
        QMessageBox.information(self, title, text)

    @Slot(QAction)
    def _change_language(self, action):
        global current_lang, lang_data
        new_lang = action.data()
        if new_lang and new_lang != current_lang:
            cf_change("language", new_lang)
            current_lang = new_lang
            lang_data = lang_load(current_lang)
            self._retranslate_ui()
            self._populate_monitor_combo()

    @Slot(QAction)
    def _change_theme(self, action):
        """テーマ設定を変更し適用"""
        new_theme = action.data()
        if new_theme and new_theme != self.current_theme:
            self.current_theme = new_theme
            cf_change("theme", new_theme)
            load_and_apply_theme(new_theme) # スタイルシート適用

    def set_controls_enabled(self, enabled):
        self.size_slider.setEnabled(enabled)
        self.alpha_slider.setEnabled(enabled)
        self.position_preview.setEnabled(enabled)
        self.pos_x_slider.setEnabled(enabled)
        self.pos_y_slider.setEnabled(enabled)
        self.monitor_combo.setEnabled(True)

    @Slot()
    def select_image(self):
        start_dir = os.path.dirname(self.image_path) if self.image_path else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, get_text("select_image_dialog_title"), start_dir, get_text("image_files_filter")
        )
        if file_path:
            self.image_path = file_path
            self.last_image_path = file_path
            self.path_label.setText(os.path.basename(file_path))
            self.overlay_window.set_image(self.image_path)
            is_image_loaded = self.overlay_window.original_pixmap is not None
            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)
            if is_image_loaded:
                # 内部状態に基づいてUIとOverlayを更新
                self._update_state_from_size_slider(self.current_size_percent)
                self._update_state_from_alpha_slider(self.current_alpha_percent)
                # update_positionは上記から呼ばれる
                if self.overlay_enabled:
                    self.overlay_window.show()
            else:
                 self.overlay_window.hide()
                 self.image_path = None
                 self.last_image_path = None

    @Slot(int)
    def toggle_overlay(self, state):
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        is_image_loaded = self.overlay_window.original_pixmap is not None
        if self.overlay_enabled and is_image_loaded:
            # 表示前に状態を適用
            self._update_state_from_size_slider(self.current_size_percent)
            self._update_state_from_alpha_slider(self.current_alpha_percent)
            # self.update_position() # 上記から呼ばれる
            self.overlay_window.show()
        else:
            self.overlay_window.hide()
        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダーの値に応じて内部状態、UI、オーバーレイを更新"""
        if self.current_size_percent == value: return
        self.current_size_percent = value
        self.size_label.setText(get_text("size_label", value=value))
        self.overlay_window.set_size_factor(value / 100.0)
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position()

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダーの値に応じて内部状態とオーバーレイを更新"""
        if self.current_alpha_percent == value: return
        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        self.overlay_window.set_alpha(value) # %を渡す

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェットでの操作に応じて内部状態とUIを更新"""
        if not self.position_preview.isEnabled(): return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()

        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

        # サイズ更新チェックと処理
        if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
            original_w = self.overlay_window.original_pixmap.width()
            if original_w > 0:
                new_percent = round((new_actual_w / original_w) * 100) # round使用
                new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
                if self.current_size_percent != new_percent:
                    size_changed = True
                    self.current_size_percent = new_percent
                    # スライダーとラベル更新 (ブロック)
                    self.size_slider.blockSignals(True)
                    self.size_slider.setValue(new_percent)
                    self.size_slider.blockSignals(False)
                    self.size_label.setText(get_text("size_label", value=new_percent))
                    # OverlayWindow係数更新
                    self.overlay_window.set_size_factor(new_percent / 100.0)

        # 位置更新チェックと処理
        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            # スライダーとラベル更新 (ブロック)
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            self._update_slider_ranges() # 範囲更新を先に行う
            self.pos_x_slider.setValue(self.current_relative_x)
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            self._update_position_labels()

        # 変更があった場合の最終処理
        if size_changed: # サイズ変更時は位置スライダー範囲も再計算
             self._update_slider_ranges()

        if position_changed or size_changed:
            # プレビュー自身の表示は操作元なので更新不要だが、
            # 位置変更時に範囲クリップが発生する可能性があるので念のため更新
            self._update_preview_widget_info()
            self.update_position() # 最終的なオーバーレイ位置適用


    @Slot()
    def _update_position_from_sliders(self):
        """位置スライダーの変更に応じて内部状態とプレビューを更新し、位置変更を実行"""
        new_rel_x = self.pos_x_slider.value()
        new_rel_y = self.pos_y_slider.value()

        if self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            self._update_position_labels()
            self._update_preview_widget_info()
            self.update_position()

    def update_position(self):
        """現在の内部相対座標からオーバーレイの絶対位置を計算・移動"""
        screen = self._get_selected_screen()
        if not screen: return
        screen_offset = screen.availableGeometry().topLeft()
        absolute_x = screen_offset.x() + self.current_relative_x
        absolute_y = screen_offset.y() + self.current_relative_y
        self.overlay_window.set_overlay_position(absolute_x, absolute_y)
        # 位置変更後、プレビューも更新 (クリップ考慮)
        self._update_preview_widget_info()

    def closeEvent(self, event):
        """メインウィンドウが閉じられるときに設定を保存"""
        try:
            cf_change("window_x", self.pos().x())
            cf_change("window_y", self.pos().y())
            cf_change("window_width", self.size().width())
            cf_change("window_height", self.size().height())
            cf_change("overlay_size", self.current_size_percent)
            cf_change("overlay_alpha", self.current_alpha_percent)
            cf_change("overlay_x", self.current_relative_x)
            cf_change("overlay_y", self.current_relative_y)
            cf_change("target_monitor_name", self.target_monitor_name)
            cf_change("last_image_path", self.last_image_path)
            cf_change("theme", self.current_theme)
        except Exception as e:
             print(f"Error saving settings: {e}", file=sys.stderr)
        self.overlay_window.close()
        event.accept()

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_instance = app # グローバル参照設定
    load_and_apply_theme(current_theme) # 初期テーマ適用
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())