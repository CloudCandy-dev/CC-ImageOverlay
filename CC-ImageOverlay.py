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
from lib.PositionPreviewWidget import PositionPreviewWidget # libからインポート

# グローバル設定の読み込み
config_data = cf_load()
current_lang = config_data.get("language", "ja")
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
        """表示する画像を設定"""
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
                # 画像がセットされたら、MainWindow側で状態に基づいて表示更新をトリガーする
        else:
            self.original_pixmap = None
            self.clear()

    def update_display(self):
        """現在の設定に基づいて表示を更新"""
        if not self.original_pixmap:
            self.clear()
            self.hide()
            return
        try:
            current_factor = self.size_factor
            # オリジナル画像のサイズから計算
            orig_w = self.original_pixmap.width()
            orig_h = self.original_pixmap.height()
            scaled_width = max(1, int(round(orig_w * current_factor))) # round追加
            scaled_height = max(1, int(round(orig_h * current_factor)))# round追加

            # 以前のPixmapと同じサイズなら再生成しない（ちらつき防止）
            if self.current_pixmap is None or self.current_pixmap.size() != QSize(scaled_width, scaled_height):
                self.current_pixmap = self.original_pixmap.scaled(
                    QSize(scaled_width, scaled_height),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(self.current_pixmap)

            self.setFixedSize(self.current_pixmap.size()) # サイズ設定は毎回行う
            self.setWindowOpacity(self.alpha_level)

            # 表示状態更新
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
        """サイズ倍率を設定 (MainWindowから呼ばれる)"""
        new_factor = max(0.01, factor)
        if abs(self.size_factor - new_factor) > 1e-6:
             self.size_factor = new_factor
             self.update_display()

    def set_alpha(self, alpha_percent):
        """透明度を設定 (0-100)"""
        new_alpha_level = max(0.0, min(1.0, alpha_percent / 100.0))
        if abs(self.alpha_level - new_alpha_level) > 1e-6:
            self.alpha_level = new_alpha_level
            self.setWindowOpacity(self.alpha_level)

    def set_overlay_position(self, x, y):
        """オーバーレイウィンドウの絶対位置を設定"""
        self.move(x, y)


class MainWindow(QMainWindow):
    """メインコントロールウィンドウ"""
    def __init__(self):
        super().__init__()

        DEFAULT_WINDOW_X = 100
        DEFAULT_WINDOW_Y = 100
        DEFAULT_WINDOW_WIDTH = 450
        DEFAULT_WINDOW_HEIGHT = 480
        DEFAULT_OVERLAY_SIZE = 100
        DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0
        DEFAULT_OVERLAY_REL_Y = 0
        DEFAULT_TARGET_MONITOR_NAME = None
        DEFAULT_LAST_IMAGE = None

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
        """メニューアクションを作成"""
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
        self.lang_ja_action = QAction("", self)
        self.lang_ja_action.setCheckable(True)
        self.lang_ja_action.setData("ja")
        if current_lang == "ja": self.lang_ja_action.setChecked(True)
        self.lang_group.addAction(self.lang_ja_action)
        self.lang_en_action = QAction("", self)
        self.lang_en_action.setCheckable(True)
        self.lang_en_action.setData("en")
        if current_lang == "en": self.lang_en_action.setChecked(True)
        self.lang_group.addAction(self.lang_en_action)

    def _create_menus(self):
        """メニューバーとメニューを作成"""
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("")
        self.info_menu = menu_bar.addMenu("")
        self.settings_menu = menu_bar.addMenu("")
        self.language_menu = self.settings_menu.addMenu("")

        self.file_menu.addAction(self.exit_action)
        self.info_menu.addAction(self.help_action)
        self.info_menu.addSeparator()
        self.info_menu.addAction(self.version_action)
        self.info_menu.addAction(self.license_action)
        self.language_menu.addAction(self.lang_ja_action)
        self.language_menu.addAction(self.lang_en_action)

    def _create_widgets(self):
        """メインウィンドウのウィジェットを作成"""
        self.select_button = QPushButton()
        self.path_label = QLabel()
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
        """ウィジェットをレイアウトに配置"""
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
        row += 1
        control_layout.addWidget(self.alpha_label, row, 0)
        control_layout.addWidget(self.alpha_slider, row, 1, 1, 2)

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
        # スライダーに初期値を反映
        self.alpha_slider.setValue(self.current_alpha_percent)
        self.size_slider.setValue(self.current_size_percent)
        self.pos_x_slider.setValue(self.current_relative_x)
        self.pos_y_slider.setValue(self.current_relative_y)

        # プレビューとスライダー範囲を初期化
        self._update_preview_widget_info()
        self._update_slider_ranges()

        # コントロール初期状態
        self.set_controls_enabled(False)
        self.enable_checkbox.setEnabled(False)

        # 前回画像読み込み
        if self.last_image_path and os.path.exists(self.last_image_path):
            self.image_path = self.last_image_path
            self.path_label.setText(os.path.basename(self.image_path))
            self.overlay_window.set_image(self.image_path) # ここで original_pixmap 設定
            if self.overlay_window.original_pixmap:
                self.enable_checkbox.setEnabled(True)
                # 内部状態を OverlayWindow に適用し、関連UIを更新
                self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
                self.overlay_window.set_alpha(self.current_alpha_percent)
                self._update_slider_ranges()
                self._update_preview_widget_info()
                self.update_position() # 位置適用
            else:
                # 画像ロード失敗時
                self.image_path = None
                self.last_image_path = None
                self.path_label.setText(get_text("no_image_selected"))
        else:
             self.path_label.setText(get_text("no_image_selected"))

        # 最終的なコントロール有効状態
        is_image_loaded = self.overlay_window.original_pixmap is not None
        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)


    def _populate_monitor_combo(self):
        """モニター選択コンボボックスに項目を追加し、以前の設定を選択"""
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
            if saved_monitor_name == screen.name():
                selected_index = i
            elif saved_monitor_name is None and screen.name() == primary_screen_name:
                 selected_index = i

        if selected_index != -1:
             self.monitor_combo.setCurrentIndex(selected_index)
             current_selection_name = self.monitor_combo.itemData(selected_index)
        elif self.monitor_combo.count() > 0:
            self.monitor_combo.setCurrentIndex(0)
            current_selection_name = self.monitor_combo.itemData(0)

        self.target_monitor_name = current_selection_name
        self.monitor_combo.blockSignals(False)


    def _get_selected_screen(self) -> QScreen | None:
        """コンボボックスで選択されているQScreenオブジェクトを取得"""
        selected_name = self.monitor_combo.currentData()
        if selected_name:
            for screen in self.screens:
                if screen.name() == selected_name:
                    return screen
        if self.screens:
             primary = QApplication.primaryScreen()
             if primary: return primary
             if self.screens: return self.screens[0] # リストがあれば先頭
        return None

    def _update_slider_ranges(self):
        """選択中のモニターとオーバーレイサイズに基づいて位置スライダー範囲を更新"""
        screen = self._get_selected_screen()
        if not screen: return

        screen_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()

        max_x = max(0, screen_geom.width() - overlay_w)
        max_y = max(0, screen_geom.height() - overlay_h)

        # スライダー範囲更新前に値を調整
        self.current_relative_x = min(self.current_relative_x, max(0, max_x))
        self.current_relative_y = min(self.current_relative_y, max(0, max_y))

        self.pos_x_slider.blockSignals(True)
        self.pos_y_slider.blockSignals(True)
        self.pos_x_slider.setRange(0, max(0, max_x))
        self.pos_y_slider.setRange(0, max(0, max_y))
        self.pos_x_slider.setValue(self.current_relative_x) # 調整後の値を設定
        self.pos_y_slider.setValue(self.current_relative_y) # 調整後の値を設定
        self.pos_x_slider.blockSignals(False)
        self.pos_y_slider.blockSignals(False)

        self._update_position_labels()

    def _get_current_overlay_actual_size(self) -> tuple[int, int]:
        """現在の内部状態からオーバーレイの実際のピクセルサイズを計算"""
        overlay_w = 50
        overlay_h = 50
        current_factor = self.current_size_percent / 100.0
        if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
             orig_w = self.overlay_window.original_pixmap.width()
             orig_h = self.overlay_window.original_pixmap.height()
             if orig_w > 0 and orig_h > 0:
                 overlay_w = int(round(orig_w * current_factor)) # round追加
                 overlay_h = int(round(orig_h * current_factor)) # round追加
        return max(1, overlay_w), max(1, overlay_h)

    def _update_preview_widget_info(self):
        """プレビューウィジェットに必要な情報を渡して更新"""
        screen = self._get_selected_screen()
        if not screen: return

        monitor_geom = screen.availableGeometry()
        overlay_w, overlay_h = self._get_current_overlay_actual_size()

        self.position_preview.setMonitorGeometry(monitor_geom.width(), monitor_geom.height())
        self.position_preview.setOverlayInfo(self.current_relative_x, self.current_relative_y, overlay_w, overlay_h)

    def _update_position_labels(self):
        """現在の相対座標で位置ラベルを更新"""
        self.pos_x_label.setText(get_text("pos_x_label", value=self.current_relative_x))
        self.pos_y_label.setText(get_text("pos_y_label", value=self.current_relative_y))

    @Slot()
    def _on_monitor_selected(self):
        """モニター選択が変更されたときの処理"""
        new_monitor_name = self.monitor_combo.currentData()
        if new_monitor_name and new_monitor_name != self.target_monitor_name:
             self.target_monitor_name = new_monitor_name
             # モニターが変わったら範囲・プレビュー・位置を再計算
             self._update_slider_ranges()
             self._update_preview_widget_info()
             self.update_position()

    def _retranslate_ui(self):
        """UI要素のテキストを現在の言語で更新"""
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
        self.select_button.setText(get_text("select_image_button"))
        if not self.image_path:
            self.path_label.setText(get_text("no_image_selected"))
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
        text = get_text("version_text")
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

    def set_controls_enabled(self, enabled):
        """画像関連のコントロールの有効/無効を切り替え"""
        self.size_slider.setEnabled(enabled)
        self.alpha_slider.setEnabled(enabled)
        self.position_preview.setEnabled(enabled)
        self.pos_x_slider.setEnabled(enabled)
        self.pos_y_slider.setEnabled(enabled)
        self.monitor_combo.setEnabled(True)

    @Slot()
    def select_image(self):
        """画像ファイル選択ダイアログを開く"""
        start_dir = os.path.dirname(self.image_path) if self.image_path else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, get_text("select_image_dialog_title"), start_dir, get_text("image_files_filter")
        )
        if file_path:
            self.image_path = file_path
            self.last_image_path = file_path
            self.path_label.setText(os.path.basename(file_path))
            self.overlay_window.set_image(self.image_path) # Loads original_pixmap

            is_image_loaded = self.overlay_window.original_pixmap is not None
            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)

            if is_image_loaded:
                # 画像ロード後、現在のUI状態（スライダー値など）で表示を更新開始
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
        """オーバーレイ表示のON/OFFを切り替え"""
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        is_image_loaded = self.overlay_window.original_pixmap is not None
        if self.overlay_enabled and is_image_loaded:
            # 表示前に現在の状態で更新
            self._update_state_from_size_slider(self.current_size_percent)
            self._update_state_from_alpha_slider(self.current_alpha_percent)
            # self.update_position() # 上記から呼ばれる
            self.overlay_window.show()
        else:
            self.overlay_window.hide()
        # コントロール有効状態更新
        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダーの値に応じて内部状態、UI、オーバーレイを更新"""
        # 値が実際に変わったかチェック
        if self.current_size_percent == value: return

        self.current_size_percent = value
        self.size_label.setText(get_text("size_label", value=value))
        # OverlayWindowのサイズ係数を更新 -> update_displayが呼ばれる
        self.overlay_window.set_size_factor(value / 100.0)
        # サイズ変更に伴う再計算・更新
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position()

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダーの値に応じて内部状態とオーバーレイを更新"""
        if self.current_alpha_percent == value: return

        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        # OverlayWindowの透明度を更新 (%で渡す)
        self.overlay_window.set_alpha(value)

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェットでの操作に応じて内部状態とUIを更新"""
        if not self.position_preview.isEnabled(): return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()

        # 変更があったかどうかのフラグ
        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

        # サイズ更新処理 (パーセンテージ計算)
        if self.overlay_window.original_pixmap and not self.overlay_window.original_pixmap.isNull():
            original_w = self.overlay_window.original_pixmap.width()
            if original_w > 0:
                # round() を使用して丸め誤差を軽減
                new_percent = round((new_actual_w / original_w) * 100)
                new_percent = max(self.size_slider.minimum(), min(new_percent, self.size_slider.maximum()))
                # パーセンテージが実際に変わった場合のみ更新
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

        # 位置更新処理
        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            # スライダー更新 (ブロック)
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            # 範囲チェックは _update_slider_ranges で行われるので不要かも
            self.pos_x_slider.setValue(self.current_relative_x)
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            # ラベル更新
            self._update_position_labels()

        # 変更があった場合の最終処理
        if size_changed: # サイズが変わった場合のみ位置スライダー範囲再計算
             self._update_slider_ranges()

        if position_changed or size_changed:
            # プレビューウィジェット自身の情報は最新なので再更新は不要
            # self._update_preview_widget_info()
            self.update_position() # 最終的なオーバーレイ位置適用

    @Slot()
    def _update_position_from_sliders(self):
        """位置スライダーの変更に応じて内部状態とプレビューを更新し、位置変更を実行"""
        new_rel_x = self.pos_x_slider.value()
        new_rel_y = self.pos_y_slider.value()

        # 内部状態と比較して、実際に変化があった場合のみ処理
        if self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y

            self._update_position_labels()
            self._update_preview_widget_info() # スライダー変更時はプレビューも更新
            self.update_position() # 位置更新

    def update_position(self):
        """現在の内部相対座標からオーバーレイの絶対位置を計算・移動"""
        screen = self._get_selected_screen()
        if not screen: return

        screen_offset = screen.availableGeometry().topLeft()
        absolute_x = screen_offset.x() + self.current_relative_x
        absolute_y = screen_offset.y() + self.current_relative_y

        self.overlay_window.set_overlay_position(absolute_x, absolute_y)
        # 位置変更後にプレビュー情報も更新（位置がクリップされる可能性があるため）
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
        except Exception as e:
             print(f"Error saving settings: {e}", file=sys.stderr)

        self.overlay_window.close()
        event.accept()

# --- アプリケーションの実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())