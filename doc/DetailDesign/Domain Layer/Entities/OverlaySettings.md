# OverlaySettings 詳細設計

## 1. 概要
オーバーレイウィンドウの状態と設定を管理するエンティティクラス。位置、サイズ、透明度、モード、メモ設定などを保持する。

## 2. クラス定義

```python
class OverlaySettings:
    """オーバーレイ設定クラス"""
    
    def __init__(self):
        self._position = QPoint(0, 0)
        self._size = 400  # 縦横比固定のため単一の値
        self._opacity = 0.8
        self._is_visible = False
        self._mode = OverlayMode.IMAGE
        self._monitor = "primary"
        self._memo_text = ""
        self._memo_settings = {
            "font_size": 14,
            "background_color": "#000000",
            "text_color": "#FFFFFF"
        }

    @property
    def position(self) -> QPoint:
        """オーバーレイの位置を取得"""
        return self._position

    @position.setter
    def position(self, value: tuple[int, int]) -> None:
        """オーバーレイの位置を設定"""
        self._position = QPoint(*value)

    @property
    def size(self) -> int:
        """オーバーレイのサイズを取得"""
        return self._size

    @size.setter
    def size(self, value: int) -> None:
        """オーバーレイのサイズを設定"""
        self._size = max(50, min(2000, value))

    @property
    def opacity(self) -> float:
        """透明度を取得"""
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        """透明度を設定"""
        self._opacity = max(0.1, min(1.0, value))

    @property
    def is_visible(self) -> bool:
        """表示状態を取得"""
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        """表示状態を設定"""
        self._is_visible = value

    @property
    def mode(self) -> OverlayMode:
        """現在のモードを取得"""
        return self._mode

    @mode.setter
    def mode(self, value: OverlayMode) -> None:
        """モードを設定"""
        self._mode = value

    @property
    def monitor(self) -> str:
        """表示モニターを取得"""
        return self._monitor

    @monitor.setter
    def monitor(self, value: str) -> None:
        """表示モニターを設定"""
        self._monitor = value

    @property
    def memo_text(self) -> str:
        """メモテキストを取得"""
        return self._memo_text

    @memo_text.setter
    def memo_text(self, value: str) -> None:
        """メモテキストを設定"""
        self._memo_text = value

    @property
    def memo_settings(self) -> dict:
        """メモ設定を取得"""
        return self._memo_settings.copy()

    def update_memo_settings(self, settings: dict) -> None:
        """メモ設定を更新"""
        if "font_size" in settings:
            self._memo_settings["font_size"] = max(8, min(72, settings["font_size"]))
        if "background_color" in settings:
            self._memo_settings["background_color"] = settings["background_color"]
        if "text_color" in settings:
            self._memo_settings["text_color"] = settings["text_color"]

    @classmethod
    def from_dict(cls, data: dict) -> 'OverlaySettings':
        """辞書から設定を生成"""
        instance = cls()
        if not data:
            return instance

        position = data.get("position", {})
        instance.position = (position.get("x", 0), position.get("y", 0))
        instance.size = data.get("size", 400)
        instance.opacity = data.get("opacity", 0.8)
        instance.is_visible = data.get("is_visible", False)
        instance.mode = OverlayMode(data.get("mode", "image"))
        instance.monitor = data.get("monitor", "primary")
        instance.memo_text = data.get("memo_text", "")
        if "memo_settings" in data:
            instance.update_memo_settings(data["memo_settings"])
        return instance

    def to_dict(self) -> dict:
        """設定を辞書形式に変換"""
        return {
            "position": {
                "x": self.position.x(),
                "y": self.position.y()
            },
            "size": self.size,
            "opacity": self.opacity,
            "is_visible": self.is_visible,
            "mode": self.mode.value,
            "monitor": self.monitor,
            "memo_text": self.memo_text,
            "memo_settings": self.memo_settings
        }
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from PySide6.QtCore import QPoint
from enum import Enum
```

## 4. 設定項目の詳細

### 4.1 位置設定
- x, y座標
- モニター内に収まるように制限
- モニター変更時に自動調整

### 4.2 サイズ設定
- 単一の値で縦横比を固定
- 最小: 50px
- 最大: 2000px

### 4.3 透明度設定
- 範囲: 0.1 ～ 1.0
- デフォルト: 0.8

### 4.4 メモ設定
- フォントサイズ: 8pt ～ 72pt
- 背景色: カラーコード（透明対応）
- 文字色: カラーコード（透明対応）

## 5. バリデーション

### 5.1 位置の検証
- モニター範囲内に収まるように調整
- 無効な値の場合は中央配置

### 5.2 サイズの検証
- 最小・最大範囲内に制限
- 無効な値は適切な範囲に丸める

### 5.3 透明度の検証
- 0.1 ～ 1.0の範囲に制限
- 範囲外の値は最近接の有効値に丸める

### 5.4 メモ設定の検証
- フォントサイズの範囲チェック
- カラーコードの形式検証
- 不正な値はデフォルト値で補完

## 6. シリアライズ

### 6.1 JSON変換
- from_dict: JSON辞書から設定オブジェクトを生成
- to_dict: 設定オブジェクトをJSON辞書に変換
- 不正な値は適切なデフォルト値で補完

## 7. エラー処理

### 7.1 想定されるエラー
- 無効な座標値
- 範囲外のサイズ・透明度
- 不正なカラーコード
- 無効なモニター指定

### 7.2 エラー処理方針
- 無効な値はデフォルト値または有効範囲内の値に自動補正
- エラーログを出力
- クリティカルなエラーは発生しない設計
