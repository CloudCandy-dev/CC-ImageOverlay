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
# --- ローカルライブラリインポート ---
# 共有ライブラリ (変更しない)
from lib.cnf_loader import cf_load, cf_change
from lib.lang_loader import init_language_loader, load_language, get_text
# このアプリケーション固有のライブラリ (変更可)
from lib.PositionPreviewWidget import PositionPreviewWidget

# --- グローバル変数 ---
app_instance = None      # QApplicationインスタンス参照
config_data = None       # 設定データ辞書
current_lang = "ja"      # 現在の言語コード
current_theme = "system" # 現在のテーマ名

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
                print(f"警告: テーマファイルが見つかりません: {qss_file}", file=sys.stderr)
        except Exception as e:
            # get_textが利用可能か不確かなので、ここでは直接エラーメッセージ
            print(f"テーマファイル読み込みエラー '{theme_name}.qss': {e}", file=sys.stderr)
            # エラー時はデフォルトテーマに戻すか、qssを空にする
            qss = ""
            # 安全のため、ここでメッセージボックスは表示しない (MainWindow初期化前かもしれない)

    try:
        app_instance.setStyleSheet(qss)
    except Exception as e:
         print(f"エラー: テーマ '{theme_name}' のスタイルシート適用中にエラー: {e}", file=sys.stderr)

# --- 初期設定読み込み ---
config_data = cf_load()
current_lang = config_data.get("language", "ja")
current_theme = config_data.get("theme", "system")
# 言語ローダー初期化 (cf_loadの後、MainWindow作成前)
# ここで init_language_loader を呼ぶように変更
init_language_loader(config_data)


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
                    status_text = get_text("error_loading_image_failed", image_path=os.path.basename(image_path))
                    self.main_window.statusBar().showMessage(status_text, 5000)
                self.original_pixmap = None
                self.clear()
            else:
                if self.main_window:
                     status_text = get_text("status_image_loaded", filename=os.path.basename(image_path))
                     self.main_window.statusBar().showMessage(status_text, 3000)
                # 画像読み込み成功時、表示更新は update_display に任せる
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

            # サイズが変わった場合のみPixmap再生成
            if self.current_pixmap is None or self.current_pixmap.size() != new_size:
                self.current_pixmap = self.original_pixmap.scaled(
                    new_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(self.current_pixmap)

            self.setFixedSize(new_size)
            self.setWindowOpacity(self.alpha_level)

            # 表示/非表示制御
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
             self.update_display() # サイズ変更時は表示全体を更新

    def set_alpha(self, alpha_percent):
        """透明度を設定し、表示を更新"""
        new_alpha_level = max(0.0, min(1.0, alpha_percent / 100.0))
        if abs(self.alpha_level - new_alpha_level) > 1e-6:
            self.alpha_level = new_alpha_level
            self.setWindowOpacity(self.alpha_level) # 透明度のみ直接設定

    def set_overlay_position(self, x, y):
        """ウィンドウ位置を設定"""
        self.move(x, y)


class MainWindow(QMainWindow):
    """メインコントロールウィンドウクラス"""
    def __init__(self):
        """コンストラクタ"""
        super().__init__()
        global config_data # グローバル設定データを参照

        # --- 定数 (デフォルト値) ---
        DEFAULT_WINDOW_X = 100; DEFAULT_WINDOW_Y = 100
        DEFAULT_WINDOW_WIDTH = 450; DEFAULT_WINDOW_HEIGHT = 480
        DEFAULT_OVERLAY_SIZE = 100; DEFAULT_OVERLAY_ALPHA = 100
        DEFAULT_OVERLAY_REL_X = 0; DEFAULT_OVERLAY_REL_Y = 0
        DEFAULT_TARGET_MONITOR_NAME = None; DEFAULT_LAST_IMAGE = None
        DEFAULT_THEME = "system"

        # --- 内部状態変数 ---
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
        self.overlay_enabled = False # 初期状態は非表示
        self.image_path = None       # 初期状態は画像なし

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
        self._retranslate_ui()       # UIテキスト設定 (get_textを使用)
        self._initialize_ui_state()  # UI初期状態設定

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
        self._populate_monitor_combo() # モニター情報読み込み
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
        # control_layout.setRowStretch(row, 1) # 必要ならプレビュー行の伸縮設定
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

        self._update_preview_widget_info() # 先にプレビュー情報更新
        self._update_slider_ranges()       # 次にスライダー範囲更新

        self.set_controls_enabled(False)   # 初期はコントロール無効
        self.enable_checkbox.setEnabled(False) # チェックボックスも無効

        is_image_loaded = False
        if self.last_image_path and os.path.exists(self.last_image_path):
            self.image_path = self.last_image_path
            self.path_label.setText(os.path.basename(self.image_path))
            self.overlay_window.set_image(self.image_path)
            if self.overlay_window.original_pixmap:
                is_image_loaded = True
            else:
                self.image_path = None
                self.last_image_path = None
                self.path_label.setText(get_text("no_image_selected"))
        else:
             self.path_label.setText(get_text("no_image_selected"))

        self.set_controls_enabled(is_image_loaded)
        self.enable_checkbox.setEnabled(is_image_loaded)

        if is_image_loaded:
            # 初期値をオーバーレイウィンドウに適用
            self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
            self.overlay_window.set_alpha(self.current_alpha_percent)
            # スライダー範囲とプレビューを再更新 (サイズ設定後)
            self._update_slider_ranges()
            self._update_preview_widget_info()
            # 初期位置を設定 (非表示状態)
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
        # フォールバック
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
        # Clamp current values before setting range/value
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
        global current_lang
        new_lang = action.data()
        if new_lang and new_lang != current_lang:
            cf_change("language", new_lang)
            current_lang = new_lang
            load_language(current_lang) # lang_loader の関数呼び出し
            self._retranslate_ui()
            self._populate_monitor_combo() # モニター名も再設定

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
        self.monitor_combo.setEnabled(len(self.screens) > 0) # モニター選択は常に有効

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
            self.path_label.setText(os.path.basename(file_path))
            self.overlay_window.set_image(self.image_path) # 画像読み込み試行

            is_image_loaded = self.overlay_window.original_pixmap is not None

            self.enable_checkbox.setEnabled(is_image_loaded)
            self.set_controls_enabled(is_image_loaded)

            if is_image_loaded:
                # 読み込み成功したら現在の設定値を適用
                self.overlay_window.set_size_factor(self.current_size_percent / 100.0)
                self.overlay_window.set_alpha(self.current_alpha_percent)
                # スライダー範囲とプレビュー更新
                self._update_slider_ranges()
                self._update_preview_widget_info()
                # 初期位置設定 (重要: 表示状態に関わらず位置を設定する)
                self.update_position()
                # チェックボックスの状態に応じて表示/非表示
                if self.overlay_enabled:
                    self.overlay_window.show()
                else:
                    self.overlay_window.hide()
            else:
                 # 読み込み失敗
                 self.overlay_window.hide()
                 self.image_path = None
                 self.last_image_path = None
                 self.path_label.setText(get_text("no_image_selected"))


    @Slot(int)
    def toggle_overlay(self, state):
        """表示チェックボックス状態変更処理 (バグ修正適用)"""
        self.overlay_enabled = (state == Qt.CheckState.Checked.value)
        is_image_loaded = self.image_path is not None and self.overlay_window.original_pixmap is not None

        # チェックオン かつ 画像ロード済みなら表示、それ以外は非表示
        if self.overlay_enabled and is_image_loaded:
            # 位置や外観は select_image やスライダー操作で設定済みのはず
            self.overlay_window.show()
        else:
            self.overlay_window.hide()


    @Slot(int)
    def _update_state_from_size_slider(self, value):
        """サイズスライダー変更処理"""
        if self.current_size_percent == value: return
        self.current_size_percent = value
        self.size_label.setText(get_text("size_label", value=value))
        self.overlay_window.set_size_factor(value / 100.0)
        self._update_slider_ranges()
        self._update_preview_widget_info()
        self.update_position() # 位置も更新

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

        # # 以前のバグ修正箇所 (不要になった)
        # if not self.overlay_enabled or not self.image_path or not self.overlay_window.original_pixmap:
        #      return

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
                    self.overlay_window.set_size_factor(new_percent / 100.0) # 表示更新含む

        if position_changed:
            self.current_relative_x = new_rel_x
            self.current_relative_y = new_rel_y
            # スライダー範囲更新 -> 値設定 -> ラベル更新 の順が安全
            self._update_slider_ranges() # スライダー範囲更新（ここで値がクリップされる可能性）
            self.pos_x_slider.blockSignals(True)
            self.pos_y_slider.blockSignals(True)
            self.pos_x_slider.setValue(self.current_relative_x) # クリップ後の値を設定
            self.pos_y_slider.setValue(self.current_relative_y)
            self.pos_x_slider.blockSignals(False)
            self.pos_y_slider.blockSignals(False)
            self._update_position_labels()

        if size_changed:
             self._update_slider_ranges() # サイズ変更時も範囲更新

        if position_changed or size_changed:
            # プレビュー自身の表示はドラッグ中に更新されているが、
            # クリップ等で内部状態とずれる可能性があるので最終状態で再設定
            self._update_preview_widget_info()
            # 最終的なオーバーレイ位置適用
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
        """オーバーレイウィンドウの絶対位置計算・移動 (バグ修正適用)"""
        # --- 修正: overlay_enabled のチェックを削除 ---
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
            cf_change("window_x", self.pos().x())
            cf_change("window_y", self.pos().y())
            cf_change("window_width", self.size().width())
            cf_change("window_height", self.size().height())
            cf_change("overlay_size", self.current_size_percent)
            cf_change("overlay_alpha", self.current_alpha_percent)
            cf_change("overlay_x", self.current_relative_x)
            cf_change("overlay_y", self.current_relative_y)
            cf_change("target_monitor_name", self.target_monitor_name)
            # 有効な画像パスのみ保存
            if self.image_path and os.path.exists(self.image_path):
                 cf_change("last_image_path", self.image_path)
            else:
                 cf_change("last_image_path", "")
            cf_change("theme", self.current_theme)
            print("設定を保存しました。")
        except Exception as e:
             print(f"設定保存中にエラーが発生しました: {e}", file=sys.stderr)
        self.overlay_window.close()
        event.accept()

# --- アプリケーション実行 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_instance = app
    # 初期テーマ適用 (MainWindow作成前)
    load_and_apply_theme(current_theme)
    # メインウィンドウ作成・表示
    main_win = MainWindow()
    main_win.show()
    # イベントループ開始
    sys.exit(app.exec())