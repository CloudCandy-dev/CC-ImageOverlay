# ImageProcessor 詳細設計

## 1. 概要
画像処理を担当するクラス。画像の読み込み、サイズ変更、回転などの基本的な画像処理機能を提供する。また、将来的な拡張性を考慮したプラグインシステムのベースとなる。

## 2. クラス定義

```python
class ImageProcessor:
    """画像処理クラス"""
    
    def __init__(self):
        self._current_image = None
        self._original_image = None
        self._processing_cache = {}

    @property
    def current_image(self) -> QImage:
        """現在の処理済み画像を取得"""
        return self._current_image

    def load_image(self, file_path: str) -> bool:
        """画像ファイルを読み込み"""
        try:
            image = QImage(file_path)
            if image.isNull():
                logger.error(f"画像の読み込みに失敗: {file_path}")
                return False
            
            self._original_image = image
            self._current_image = image.copy()
            self._processing_cache.clear()
            return True
        except Exception as e:
            logger.error(f"画像読み込み中にエラーが発生: {e}")
            return False

    def resize_image(self, width: int, height: int, keep_aspect: bool = True) -> bool:
        """画像のリサイズ処理"""
        if not self._current_image:
            return False

        try:
            if keep_aspect:
                self._current_image = self._current_image.scaled(
                    width, height, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                self._current_image = self._current_image.scaled(
                    width, height,
                    Qt.TransformationMode.SmoothTransformation
                )
            return True
        except Exception as e:
            logger.error(f"リサイズ処理中にエラーが発生: {e}")
            return False

    def rotate_image(self, angle: float) -> bool:
        """画像の回転処理"""
        if not self._current_image:
            return False

        # キャッシュをチェック
        cache_key = f"rotate_{angle}"
        if cache_key in self._processing_cache:
            self._current_image = self._processing_cache[cache_key]
            return True

        try:
            transform = QTransform()
            transform.rotate(angle)
            rotated = self._current_image.transformed(
                transform,
                Qt.TransformationMode.SmoothTransformation
            )
            self._current_image = rotated
            # キャッシュに保存
            self._processing_cache[cache_key] = rotated
            return True
        except Exception as e:
            logger.error(f"回転処理中にエラーが発生: {e}")
            return False

    def reset_image(self) -> bool:
        """画像を元の状態にリセット"""
        if not self._original_image:
            return False
        
        self._current_image = self._original_image.copy()
        self._processing_cache.clear()
        return True

    def clear(self) -> None:
        """全ての画像データをクリア"""
        self._current_image = None
        self._original_image = None
        self._processing_cache.clear()

    def get_supported_formats(self) -> list[str]:
        """サポートされている画像形式のリストを取得"""
        return ["png", "jpg", "jpeg", "bmp", "webp"]
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QTransform
from ..services.logging_service import logger
```

## 4. 主要メソッドの処理詳細

### 4.1 画像読み込み処理（load_image）
1. 画像ファイルの存在確認
2. QImageによる画像の読み込み
3. 画像の有効性チェック
4. オリジナル画像の保存
5. 現在の画像としてコピーを作成

### 4.2 リサイズ処理（resize_image）
1. 入力パラメータの検証
2. アスペクト比の維持有無の確認
3. スムーズ変換モードでのリサイズ実行
4. エラー発生時の適切な処理

### 4.3 回転処理（rotate_image）
1. キャッシュの確認
2. 変換マトリックスの作成
3. スムーズ変換モードでの回転実行
4. 結果のキャッシュへの保存

## 5. エラー処理

### 5.1 想定されるエラー
- ファイル読み込み失敗
- メモリ不足
- 無効な画像形式
- 無効なサイズ指定
- 処理中の例外発生

### 5.2 エラー処理方針
- ファイルエラー → エラーログ記録とfalse返却
- メモリエラー → 処理中断とログ記録
- パラメータエラー → デフォルト値使用または処理中断
- 処理エラー → 元の状態を維持

## 6. スレッド安全性

- 画像処理は時間がかかる可能性があるため、必要に応じて別スレッドで実行
- キャッシュへのアクセスは排他制御を実装
- QImageは暗黙的なデータ共有を使用

## 7. パフォーマンス考慮事項

- 回転処理結果のキャッシュ化
- メモリ使用量の最適化
  - 大きな画像の段階的な読み込み
  - 未使用キャッシュの定期的なクリーンアップ
- 画質と処理速度のバランス調整
  - スムーズ変換モードの適切な使用
  - 必要に応じた画質調整
