# ImageUtils 詳細設計

## 1. 概要
画像処理に関する共通ユーティリティ機能を提供するクラス。画像の変換、サイズ調整、フォーマット変更、最適化などの機能を提供する。

## 2. クラス定義

```python
class ImageUtils:
    """画像処理ユーティリティクラス"""
    
    @staticmethod
    def resize_image(image: QImage, width: int, height: int, 
                    keep_aspect: bool = True) -> QImage:
        """画像のリサイズ処理"""
        try:
            if not image or image.isNull():
                return QImage()

            if keep_aspect:
                return image.scaled(width, height, 
                                 Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.SmoothTransformation)
            return image.scaled(width, height, 
                              Qt.AspectRatioMode.IgnoreAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            logger.error(f"画像リサイズに失敗: {e}")
            return QImage()

    @staticmethod
    def convert_format(image: QImage, format: QImage.Format) -> QImage:
        """画像フォーマットの変換"""
        try:
            if not image or image.isNull():
                return QImage()

            if image.format() == format:
                return image.copy()
            return image.convertToFormat(format)
        except Exception as e:
            logger.error(f"フォーマット変換に失敗: {e}")
            return QImage()

    @staticmethod
    def adjust_opacity(image: QImage, opacity: int) -> QImage:
        """画像の透明度調整"""
        try:
            if not image or image.isNull():
                return QImage()

            if opacity == 255:
                return image.copy()

            if image.format() != QImage.Format_ARGB32:
                image = image.convertToFormat(QImage.Format_ARGB32)

            result = QImage(image.size(), QImage.Format_ARGB32)
            painter = QPainter(result)
            painter.setOpacity(opacity / 255.0)
            painter.drawImage(0, 0, image)
            painter.end()
            return result

        except Exception as e:
            logger.error(f"透明度調整に失敗: {e}")
            return QImage()

    @staticmethod
    def rotate_image(image: QImage, angle: float) -> QImage:
        """画像の回転処理"""
        try:
            if not image or image.isNull():
                return QImage()

            transform = QTransform().rotate(angle)
            return image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            logger.error(f"画像回転に失敗: {e}")
            return QImage()

    @staticmethod
    def optimize_image(image: QImage, 
                      max_size: int = 1920,
                      quality: int = 85) -> QImage:
        """画像の最適化処理"""
        try:
            if not image or image.isNull():
                return QImage()

            # サイズの最適化
            if image.width() > max_size or image.height() > max_size:
                image = ImageUtils.resize_image(image, max_size, max_size)

            # メモリ使用量の最適化
            if image.format() not in [QImage.Format_RGB32, QImage.Format_ARGB32]:
                image = image.convertToFormat(QImage.Format_RGB32)

            return image
        except Exception as e:
            logger.error(f"画像最適化に失敗: {e}")
            return QImage()

    @staticmethod
    def create_thumbnail(image: QImage, 
                        size: int = 150,
                        cache: bool = True) -> QImage:
        """サムネイル画像の生成"""
        try:
            if not image or image.isNull():
                return QImage()

            thumb = ImageUtils.resize_image(image, size, size)
            if not cache:
                return thumb

            # キャッシュ用に最適化
            if thumb.format() != QImage.Format_RGB32:
                thumb = thumb.convertToFormat(QImage.Format_RGB32)

            return thumb
        except Exception as e:
            logger.error(f"サムネイル生成に失敗: {e}")
            return QImage()

    @staticmethod
    def get_image_info(image: QImage) -> Dict[str, any]:
        """画像情報の取得"""
        try:
            if not image or image.isNull():
                return {}

            return {
                'width': image.width(),
                'height': image.height(),
                'format': str(image.format()),
                'depth': image.depth(),
                'size_bytes': image.sizeInBytes(),
                'has_alpha': image.hasAlphaChannel()
            }
        except Exception as e:
            logger.error(f"画像情報の取得に失敗: {e}")
            return {}
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QTransform
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 画像変換処理
1. サイズ変更
2. フォーマット変換
3. 透明度調整
4. 回転処理
5. 最適化処理

### 4.2 画質制御
1. アスペクト比の維持
2. スムージング処理
3. 画質パラメータ
4. メモリ使用量
5. パフォーマンス最適化

### 4.3 エラー処理
1. 入力検証
2. 例外ハンドリング
3. エラーログ記録
4. フォールバック処理
5. リソース解放

## 5. パフォーマンス最適化

### 5.1 メモリ管理
- キャッシュ制御
- リソース解放
- メモリ使用量監視
- 一時オブジェクト削除
- GC連携

### 5.2 処理速度
- 適切なアルゴリズム選択
- 並列処理の検討
- バッファリング活用
- 事前計算の利用
- 遅延処理の実装

## 6. スレッド安全性

### 6.1 並列処理
- 静的メソッドの利用
- イミュータブルな操作
- スレッドローカルな処理
- リソースの分離
- 競合の回避

### 6.2 リソース保護
- 一時オブジェクトの管理
- ペインターの適切な解放
- メモリリークの防止
- 例外時の後処理
- デッドロック防止

## 7. 画像フォーマット

### 7.1 対応フォーマット
- RGB32
- ARGB32
- RGB888
- Grayscale8
- Indexed8

### 7.2 変換ルール
- 色深度の保持
- アルファチャンネル処理
- カラーマップ変換
- ビット深度変更
- フォーマット最適化

## 8. 制約事項

### 8.1 サイズ制限
- 最大画像サイズ
- メモリ使用量
- 処理時間制限
- キャッシュサイズ
- スタック使用量

### 8.2 品質制限
- 圧縮品質範囲
- アスペクト比制限
- 回転角度制限
- 透明度範囲
- 補間方式
