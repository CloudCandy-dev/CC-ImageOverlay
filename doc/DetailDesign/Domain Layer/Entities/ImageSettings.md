# ImageSettings 詳細設計

## 1. 概要
画像処理に関連する設定を管理するエンティティクラス。画像の読み込み、リサイズ、キャッシュなどの設定を保持する。

## 2. クラス定義

```python
class ImageSettings:
    """画像設定クラス"""
    
    def __init__(self):
        self._supported_formats = [
            "png", "jpg", "jpeg", "bmp", "gif"
        ]
        self._max_image_size = 4096  # 最大画像サイズ（ピクセル）
        self._resize_quality = Qt.SmoothTransformation  # リサイズ品質
        self._cache_enabled = True
        self._cache_size = 10  # キャッシュする画像の最大数

    @property
    def supported_formats(self) -> list[str]:
        """サポートする画像形式を取得"""
        return self._supported_formats.copy()

    @property
    def max_image_size(self) -> int:
        """最大画像サイズを取得"""
        return self._max_image_size

    @max_image_size.setter
    def max_image_size(self, value: int) -> None:
        """最大画像サイズを設定"""
        self._max_image_size = max(1024, min(8192, value))

    @property
    def resize_quality(self) -> Qt.TransformationMode:
        """リサイズ品質を取得"""
        return self._resize_quality

    @resize_quality.setter
    def resize_quality(self, value: Qt.TransformationMode) -> None:
        """リサイズ品質を設定"""
        if value in [Qt.FastTransformation, Qt.SmoothTransformation]:
            self._resize_quality = value

    @property
    def cache_enabled(self) -> bool:
        """キャッシュ有効状態を取得"""
        return self._cache_enabled

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        """キャッシュ有効状態を設定"""
        self._cache_enabled = value

    @property
    def cache_size(self) -> int:
        """キャッシュサイズを取得"""
        return self._cache_size

    @cache_size.setter
    def cache_size(self, value: int) -> None:
        """キャッシュサイズを設定"""
        self._cache_size = max(1, min(50, value))

    @classmethod
    def from_dict(cls, data: dict) -> 'ImageSettings':
        """辞書から設定を生成"""
        instance = cls()
        if not data:
            return instance

        if "max_image_size" in data:
            instance.max_image_size = data["max_image_size"]
        if "resize_quality" in data:
            instance.resize_quality = Qt.TransformationMode(data["resize_quality"])
        if "cache_enabled" in data:
            instance.cache_enabled = data["cache_enabled"]
        if "cache_size" in data:
            instance.cache_size = data["cache_size"]
        return instance

    def to_dict(self) -> dict:
        """設定を辞書形式に変換"""
        return {
            "supported_formats": self.supported_formats,
            "max_image_size": self.max_image_size,
            "resize_quality": int(self.resize_quality),
            "cache_enabled": self.cache_enabled,
            "cache_size": self.cache_size
        }

    def is_supported_format(self, file_path: str) -> bool:
        """ファイルが対応フォーマットかどうかを確認"""
        ext = file_path.split('.')[-1].lower()
        return ext in self.supported_formats

    def calculate_resize_dimensions(self, original_width: int, original_height: int) -> tuple[int, int]:
        """リサイズ後のサイズを計算"""
        max_size = self.max_image_size
        if original_width <= max_size and original_height <= max_size:
            return original_width, original_height

        ratio = min(max_size / original_width, max_size / original_height)
        return int(original_width * ratio), int(original_height * ratio)
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from PySide6.QtCore import Qt
```

## 4. 設定項目の詳細

### 4.1 対応画像形式
- PNG: 透過対応の高品質画像
- JPEG: 写真などの一般的な画像
- BMP: 非圧縮の生画像
- GIF: アニメーション非対応

### 4.2 画像サイズ制限
- 最大サイズ: 1024px ～ 8192px
- デフォルト: 4096px
- 縦横どちらかが超過した場合にリサイズ

### 4.3 リサイズ品質
- Fast: 高速だが品質は低い
- Smooth: 高品質だが処理は遅い
- デフォルト: Smooth

### 4.4 キャッシュ設定
- 有効/無効の切り替え
- キャッシュサイズ: 1 ～ 50枚
- デフォルト: 10枚

## 5. バリデーション

### 5.1 画像フォーマットの検証
- 拡張子による形式チェック
- MIMEタイプによる追加確認
- 未対応形式は例外を発生

### 5.2 画像サイズの検証
- 最大サイズの範囲チェック
- リサイズ比率の計算
- アスペクト比の維持

### 5.3 キャッシュ設定の検証
- キャッシュサイズの範囲チェック
- メモリ使用量の考慮
- 無効な値の補正

## 6. リサイズアルゴリズム

### 6.1 画像の縮小
- アスペクト比を維持
- Lanczos法を使用（Qt.SmoothTransformation）
- メモリ効率を考慮

### 6.2 画質の維持
- 可能な限り元画像の品質を維持
- 透過情報の保持
- カラープロファイルの考慮

## 7. エラー処理

### 7.1 想定されるエラー
- 未対応の画像形式
- 破損した画像ファイル
- メモリ不足
- 無効なサイズ指定

### 7.2 エラー処理方針
- 画像フォーマットエラー → 例外を発生
- サイズエラー → 自動補正
- メモリ不足 → キャッシュクリア
- キャッシュエラー → 無効化して継続
