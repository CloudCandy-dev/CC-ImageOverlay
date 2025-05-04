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
from lib.cnf_loader import cf_load, cf_change
# lang_loader から必要な関数と、ロード済みのデータをインポート
from lib.lang_loader import lang_load, get_text, config_data as lang_config_data, lang_data
from lib.PositionPreviewWidget import PositionPreviewWidget

# --- グローバル変数 ---
app_instance = None # QApplication インスタンス参照
# config_data は MainWindow 内でロード・保持する方が管理しやすい
# config_data = cf_load() # ここではロードしない

# --- 関数 ---
def load_and_apply_theme(theme_name):
    """指定されたテーマを読み込み適用する。"""
    global app_instance
    if not app_instance:
        print("エラー: テーマ適用時に QApplication インスタンスが見つかりません。", file=sys.stderr)
        return

    qss = ""
    if theme_name != "system":
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            theme_dir = os.path.join(script_dir, "themes")
            qss_file = os.path.join(theme_dir, f"{theme_name}.qss")

            if os.path.exists(qss_file):
                with open(qss_file, "r", encoding="utf-8") as f:
                    qss = f.read()
                print(f"テーマファイルを読み込みました: {qss_file}")
            else:
                # lang_loaderが初期化される前なのでget_textは使えない
                print(f"警告: テーマファイルが見つかりません: {qss_file}", file=sys.stderr)
                qss = ""
        except Exception as e:
            print(f"テーマファイル読み込みエラー '{theme_name}.qss': {e}", file=sys.stderr)
            qss = ""

    try:
        app_instance.setStyleSheet(qss)
    except Exception as e:
         print(f"エラー: テーマ '{theme_name}' のスタイルシート適用中にエラー: {e}", file=sys.stderr)


# --- クラス定義 ---
class OverlayWindow(QLabel):
    """画像オーバーレイ表示用ウィンドウクラス"""
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
        """画像をファイルから読み込む"""
        if image_path and os.path.exists(image_path):
            self.original_pixmap = QPixmap(image_path)
            if self.original_pixmap.isNull():
                if self.main_window:
                    try:
                        status_text = get_text("error_loading_image_failed", image_path=os.path.basename(image_path))
                        self.main_window.statusBar().showMessage(status_text, 5000)
                    except Exception: # get_textが失敗しても止めない
                         print(f"Error loading image: {os.path.basename(image_path)}", file=sys.stderr)
                self.original_pixmap = None
                self.clear()
            else:
                if self.main_window:
                    try:
                         status_text = get_text("status_image_loaded", filename=os.path.basename(image_path))
                         self.main_window.statusBar().showMessage(status_text, 3000)
                    except Exception:
                         print(f"Image loaded: {os.path.basename(image_path)}", file=sys.stderr)
        else:
            self.original_pixmap = None
            self.clear()

    def update_display(self):
        """現在の設定に基づいて表示を更新する"""
        if not self.original_pixmap:
            self.clear()
            if self.isVisible(): self.hide()
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

            # 表示/非表示制御は MainWindow の overlay_enabled に従う
            if self.main_window and self.main_window.overlay_enabled:
                 if not self.isVisible(): self.show()
            else:
                 if self.isVisible(): self.hide()
        except Exception as e:
             error_message = f"オーバーレイ表示更新中にエラー: {e}"
             if self.main_window:
                 self.main_window.statusBar().showMessage(error_message, 5000)
             print(f"{error_message}", file=sys.stderr)

    def set_size_factor(self, factor):
        """サイズ係数を設定し、表示を更新"""
        new_factor = max(0.01, factor)
        if abs(self.size_factor - new_factor) > 1e-6:
             self.size_factor = new_factor
             self.update_display()

    def set_alpha(self, alpha_percent):
        """透明度を設定し、表示を更新"""
        new_alpha_level = max(0.0, min(1.0, alpha_percent / 100.0))
        if abs(self.alpha_level - new_alpha_level) > 1e-6:
            self.alpha_level = new_alpha_level
            # 透明度変更は直接 Opacity 設定
            self.setWindowOpacity(self.alpha_level)

    def set_overlay_position(self, x, y):
        """ウィンドウ位置を設定"""
        self.move(x, y)


class MainWindow(QMainWindow):
    """メインコントロールウィンドウクラス"""
    def __init__(self):
        """コンストラクタ"""
        super().__init__()
        # MainWindow内で設定をロード
        self.config_data = cf_load()

        # --- 定数 (デフォルト値) ---
        DEFAULT_WINDOW_X = 100; DEFAULT_WINDOW_Y = 100
        # 元のデフォルト値に戻す
        DEFAULT_WINDOW_WIDTH = 450; DEFAULT_WINDOW_HEIGHT = 300
        DEFAULT_OVERLAY_SIZE = 100; DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0; DEFAULT_OVERLAY_REL_Y = 0
        DEFAULT_TARGET_MONITOR_NAME = ""; DEFAULT_LAST_IMAGE = ""
        DEFAULT_THEME = "dark"; DEFAULT_LANG = "en" # 元のデフォルト値

        # --- 内部状態変数 ---
        # 設定ファイルから読み込み、なければデフォルト値
        initial_x = self.config_data.get("window_x", DEFAULT_WINDOW_X)
        initial_y = self.config_data.get("window_y", DEFAULT_WINDOW_Y)
        initial_width = self.config_data.get("window_width", DEFAULT_WINDOW_WIDTH)
        initial_height = self.config_data.get("window_height", DEFAULT_WINDOW_HEIGHT)
        self.last_image_path = self.config_data.get("last_image_path", DEFAULT_LAST_IMAGE)
        self.current_size_percent = self.config_data.get("overlay_size", DEFAULT_OVERLAY_SIZE)
        self.current_alpha_percent = self.config_data.get("overlay_alpha", DEFAULT_OVERLAY_ALPHA)
        self.current_relative_x = self.config_data.get("overlay_x", DEFAULT_OVERLAY_REL_X)
        self.current_relative_y = self.config_data.get("overlay_y", DEFAULT_OVERLAY_REL_Y)
        self.target_monitor_name = self.config_data.get("target_monitor_name", DEFAULT_TARGET_MONITOR_NAME)
        self.current_theme = self.config_data.get("theme", DEFAULT_THEME)
        # 現在の言語は lang_loader が保持しているものを参照する方が一貫性があるかもしれないが、
        # メニューのチェック状態管理のため、ここでも持つ
        self.current_lang = self.config_data.get("language", DEFAULT_LANG)

        self.overlay_enabled = False
        self.image_path = None

        # --- ウィンドウ設定 ---
        self.setGeometry(initial_x, initial_y, initial_width, initial_height)
        self.setStatusBar(QStatusBar())
        self.screens = QApplication.screens()

        # --- 子ウィジェット作成 ---
        self.overlay_window = OverlayWindow(self)

        # --- UI初期化 ---
        self._create_actions()
        self._create_menus()
        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self._retranslate_ui()
        self._initialize_ui_state()

    def _create_actions(self):
        """メニューアクション作成"""
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
        if self.current_lang == "ja": self.lang_ja_action.setChecked(True)
        self.lang_group.addAction(self.lang_ja_action)
        self.lang_en_action = QAction("", self, checkable=True, data="en")
        if self.current_lang == "en": self.lang_en_action.setChecked(True)
        self.lang_group.addAction(self.lang_en_action)
        self.lang_cn_action = QAction("", self, checkable=True, data="cn")
        if self.current_lang == "cn": self.lang_cn_action.setChecked(True)
        self.lang_group.addAction(self.lang_cn_action)
        self.lang_kr_action = QAction("", self, checkable=True, data="kr")
        if self.current_lang == "kr": self.lang_kr_action.setChecked(True)
        self.lang_group.addAction(self.lang_kr_action)

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
        """メニューバー作成"""
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
        """シグナルとスロット接続"""
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
                self.last_image_path = None # 読み込めなければクリア

        # ラベルは最後に再翻訳で設定
        self._retranslate_ui()

        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

        if is_image_loaded:
            self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
            self.overlay_window.set_alpha(self.current_alpha_percent)
            self._update_slider_ranges()
            self._update_preview_widget_info()
            # --- バグ修正箇所 ---
            # 初期化時にも update_position を呼び、初期位置を設定する
            self.update_position()
            # --- バグ修正箇所 ここまで ---

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
        """選択中のスクリーンオブジェクト取得"""
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
        # Noneチェックを追加
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
            action.setText(get_text(f"lang_{lang_code}"))

        self.theme_menu.setTitle(get_text("action_theme"))
        for action in self.theme_group.actions():
            theme_name = action.data()
            action.setText(get_text(f"theme_{theme_name}"))

        self.select_button.setText(get_text("select_image_button"))
        # パスラベルもここで更新
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
             except Exception as e: QMessageBox.warning(self, "Error", f"ヘルプURLを開けませんでした: {e}")
        else: QMessageBox.information(self, "Help", "ヘルプURLが設定されていません。")

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
        # lang_loader 内のグローバル変数を参照・更新しないようにする
        global lang_data # lang_loader の lang_data を直接参照する必要がある場合
        new_lang = action.data()
        if new_lang and new_lang != self.current_lang:
            cf_change("language", new_lang)
            self.current_lang = new_lang # MainWindow の属性を更新
            # lang_loader の lang_load を呼び出してグローバルな lang_data を更新
            lang_data = lang_load(new_lang) # lang_load が lang_data を更新し、それを返す想定
            # lang_data が None でないかチェック (lang_loadが失敗した場合など)
            if lang_data is None:
                lang_data = {} # 安全のため空の辞書に
                print(f"エラー: 言語データ({new_lang})の読み込みに失敗しました。", file=sys.stderr)
                # エラーメッセージ表示
                QMessageBox.warning(self, "Error", f"Failed to load language: {new_lang}")
                # 必要ならデフォルト言語に戻す処理を追加
                # cf_change("language", "en")
                # self.current_lang = "en"
                # lang_data = lang_load("en")

            self._retranslate_ui()
            self._populate_monitor_combo()

    @Slot(QAction)
    def _change_theme(self, action):
        """テーマ変更処理"""
        new_theme = action.data()
        if new_theme and new_theme != self.current_theme:
            self.current_theme = new_theme
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
        """画像選択処理 (バグ修正箇所あり)"""
        start_dir = os.path.dirname(self.image_path) if self.image_path else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, get_text("select_image_dialog_title"), start_dir, get_text("image_files_filter")
        )
        if file_path:
            self.image_path = file_path
            self.last_image_path = file_path
            # self.path_label.setText(os.path.basename(file_path)) # _retranslate_ui で行う
            self.overlay_window.set_image(self.image_path)

            is_image_loaded = self.overlay_window.original_pixmap is not None

            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)

            if is_image_loaded:
                # 設定適用 -> スライダー/プレビュー更新 -> 位置更新 の順
                self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
                self.overlay_window.set_alpha(self.current_alpha_percent)
                self._update_slider_ranges()
                self._update_preview_widget_info()
                # --- バグ修正箇所 ---
                # 画像選択後、表示状態に関わらず必ず初期位置を設定する
                self.update_position()
                # --- バグ修正箇所 ここまで ---

                # チェックボックスの状態に合わせて表示/非表示
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
        """表示チェックボックス状態変更処理 (修正済み)"""
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        is_image_loaded = self.image_path is not None and self.overlay_window.original_pixmap is not None

        if self.overlay_enabled and is_image_loaded:
            # 位置は select_image やスライダー操作で設定されているはず
            self.overlay_window.show()
        else:
            self.overlay_window.hide()

    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダー変更処理"""
        if self.current_size_percent == value: return
        self.current_size_percent = value
        self.size_label.setText(get_text("size_label", value=value))
        # size_factor 設定 -> update_display 呼び出し
        self.overlay_window.set_size_factor(value / 100.0)
        # update_display 後に範囲とプレビューと位置を更新
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position()

    @Slot(int)
    def _update_state_from_alpha_slider(self, value):
        """透明度スライダー変更処理"""
        if self.current_alpha_percent == value: return
        self.current_alpha_percent = value
        self.alpha_label.setText(get_text("alpha_label", value=value))
        self.overlay_window.set_alpha(value)

    @Slot()
    def _update_controls_from_preview_geom(self):
        """プレビューウィジェット変更処理"""
        if not self.position_preview.isEnabled(): return

        new_rel_pos = self.position_preview.getOverlayRelativePos()
        new_actual_size = self.position_preview.getOverlayActualSize()
        new_rel_x = new_rel_pos.x()
        new_rel_y = new_rel_pos.y()
        new_actual_w = new_actual_size.width()

        position_changed = (self.current_relative_x != new_rel_x or self.current_relative_y != new_rel_y)
        size_changed = False

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

    def update_position(self):
        """オーバーレイウィンドウの絶対位置計算・移動 (バグ修正適用済み)"""
        # --- バグ修正: overlay_enabled チェック削除 ---
        screen = self._get_selected_screen()
        if not screen: return

        screen_geom = screen.availableGeometry()
        screen_offset = screen_geom.topLeft()

        absolute_x = screen_offset.x() + self.current_relative_x
        absolute_y = screen_offset.y() + self.current_relative_y

        self.overlay_window.set_overlay_position(absolute_x, absolute_y)

        # プレビューも更新しておく
        self._update_preview_widget_info()


    def closeEvent(self, event):
        """ウィンドウクローズイベント処理 (設定保存)"""
        try:
            # MainWindow の属性 self.config_data を更新してから保存する方が安全かもしれない
            # self.config_data['window_x'] = self.pos().x() ... のように
            # ただ、cf_change はファイルに直接書き込むのでこれでも動くはず
            cf_change("window_x", self.pos().x())
            cf_change("window_y", self.pos().y())
            cf_change("window_width", self.size().width())
            cf_change("window_height", self.size().height())
            cf_change("overlay_size", self.current_size_percent)
            cf_change("overlay_alpha", self.current_alpha_percent)
            cf_change("overlay_x", self.current_relative_x)
            cf_change("overlay_y", self.current_relative_y)
            cf_change("target_monitor_name", self.target_monitor_name)
            if self.image_path and os.path.exists(self.image_path):
                 cf_change("last_image_path", self.image_path)
            else:
                 cf_change("last_image_path", "")
            cf_change("theme", self.current_theme)
            # self.current_lang を保存
            cf_change("language", self.current_lang)
            print("設定を保存しました。")
        except Exception as e:
             print(f"設定保存中にエラーが発生しました: {e}", file=sys.stderr)
        self.overlay_window.close()
        event.accept()

# --- アプリケーション実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_instance = app
    # 初期テーマ適用 (config_data は lang_loader 内でロードされる)
    # lang_loader が保持する config_data を参照する
    initial_theme = lang_config_data.get("theme", "dark") # lang_loader の方を参照
    load_and_apply_theme(initial_theme)
    # メインウィンドウ作成・表示
    main_win = MainWindow()
    main_win.show()
    # イベントループ開始
    sys.exit(app.exec())