from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QPushButton, QSlider,
    QRadioButton, QButtonGroup, QTextEdit, QHBoxLayout
)
from PySide6.QtCore import Qt
from .lang_loader import get_text

class UIManager:
    """UI管理クラス"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.widgets = {
            'mode': {},
            'control': {},
            'detail': {},
            'memo': {}
        }
        self._create_widgets()
        self._setup_layouts()

    def _create_widgets(self):
        """全ウィジェットの作成"""
        self._create_mode_widgets()
        self._create_control_widgets()
        self._create_detail_widgets()
        self._create_memo_widgets()

    def _create_mode_widgets(self):
        """モード選択ウィジェット作成"""
        mode_widget = QWidget()
        mode_widget.setFixedHeight(32)
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(4, 4, 4, 4)
        mode_layout.setSpacing(4)

        image_radio = QRadioButton(get_text("mode_image"))
        memo_radio = QRadioButton(get_text("mode_memo"))
        image_radio.setChecked(True)
        
        mode_group = QButtonGroup(self.main_window)
        mode_group.addButton(image_radio)
        mode_group.addButton(memo_radio)

        mode_layout.addWidget(image_radio)
        mode_layout.addWidget(memo_radio)

        self.widgets['mode'].update({
            'container': mode_widget,
            'image_radio': image_radio,
            'memo_radio': memo_radio,
            'group': mode_group
        })

    def _create_control_widgets(self):
        """コントロールウィジェット作成"""
        self.widgets['control'].update({
            'select_button': QPushButton(get_text("select_image_button")),
            'path_label': QLabel(get_text("no_image_selected")),
            'enable_checkbox': QPushButton(get_text("enable_overlay_checkbox")),
            'monitor_label': QLabel(get_text("monitor_label")),
            'alpha_label': QLabel(),
            'alpha_slider': QSlider(Qt.Orientation.Horizontal)
        })

        # スライダーの設定
        self.widgets['control']['alpha_slider'].setRange(0, 100)
        self.widgets['control']['alpha_slider'].setValue(100)

    def _create_detail_widgets(self):
        """詳細設定ウィジェット作成"""
        self.widgets['detail'].update({
            'size_label': QLabel(),
            'size_slider': QSlider(Qt.Orientation.Horizontal),
            'pos_x_label': QLabel(),
            'pos_x_slider': QSlider(Qt.Orientation.Horizontal),
            'pos_y_label': QLabel(),
            'pos_y_slider': QSlider(Qt.Orientation.Horizontal),
            'bg_color_button': QPushButton(get_text("bg_color")),
            'text_color_button': QPushButton(get_text("text_color"))
        })

        # スライダーの設定
        self.widgets['detail']['size_slider'].setRange(10, 300)
        self.widgets['detail']['size_slider'].setValue(100)

    def _create_memo_widgets(self):
        """メモ関連ウィジェット作成"""
        self.widgets['memo'].update({
            'container': QWidget(),
            'content_label': QLabel(get_text("memo_content")),
            'editor': QTextEdit(),
            'font_size_label': QLabel()
        })

        self.widgets['memo']['editor'].setMinimumHeight(100)
        self.widgets['memo']['editor'].setPlaceholderText(get_text("memo_placeholder"))

    def _setup_layouts(self):
        """レイアウト設定"""
        for category in self.widgets.values():
            for widget in category.values():
                if isinstance(widget, QWidget):
                    widget.setContentsMargins(1, 1, 1, 1)

    def get_widget(self, category: str, name: str) -> QWidget:
        """ウィジェット取得"""
        return self.widgets.get(category, {}).get(name)

    def set_widget_visibility(self, category: str, name: str, visible: bool):
        """ウィジェットの表示/非表示を設定"""
        widget = self.get_widget(category, name)
        if widget:
            widget.setVisible(visible)

    def update_mode_widgets(self, is_image_mode: bool):
        """モードに応じたウィジェット表示状態を更新"""
        # イメージモード用ウィジェット
        self.set_widget_visibility('control', 'select_button', is_image_mode)
        self.set_widget_visibility('control', 'path_label', is_image_mode)

        # メモモード用ウィジェット
        memo_container = self.get_widget('memo', 'container')
        if memo_container:
            memo_container.setVisible(not is_image_mode)

        # 色設定ボタン
        self.set_widget_visibility('detail', 'bg_color_button', not is_image_mode)
        self.set_widget_visibility('detail', 'text_color_button', not is_image_mode)
