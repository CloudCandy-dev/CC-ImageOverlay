# ImageStorage 詳細設計

## 1. 概要
オーバーレイ表示に使用する画像ファイルの管理と永続化を担当するクラス。画像ファイルの読み込み、キャッシュ管理、一時ファイルの制御を行う。

## 2. クラス定義

```python
class ImageStorage:
    """画像ファイルの永続化を管理するクラス"""
    
    def __init__(self, cache_dir: str = "cache/images"):
        self._cache_dir = cache_dir
        self._temp_dir = os.path.join(cache_dir, "temp")
        self._image_cache = {}
        self._max_cache_size = 100 * 1024 * 1024  # 100MB
        self._current_cache_size = 0
        self._lock = threading.Lock()
        self._supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}

    def initialize(self) -> bool:
        """画像ストレージの初期化"""
        try:
            os.makedirs(self._cache_dir, exist_ok=True)
            os.makedirs(self._temp_dir, exist_ok=True)
            self._cleanup_temp_files()
            return True
        except Exception as e:
            logger.error(f"画像ストレージの初期化に失敗: {e}")
            return False

    def load_image(self, image_path: str) -> Optional[QImage]:
        """画像ファイルの読み込み"""
        with self._lock:
            try:
                if image_path in self._image_cache:
                    logger.debug(f"キャッシュから画像を読み込み: {image_path}")
                    return self._image_cache[image_path]

                if not os.path.exists(image_path):
                    logger.error(f"画像ファイルが存在しません: {image_path}")
                    return None

                if not self._is_supported_format(image_path):
                    logger.error(f"未対応の画像形式です: {image_path}")
                    return None

                image = QImage(image_path)
                if image.isNull():
                    logger.error(f"画像の読み込みに失敗: {image_path}")
                    return None

                self._add_to_cache(image_path, image)
                return image

            except Exception as e:
                logger.error(f"画像の読み込み中にエラーが発生: {e}")
                return None

    def save_temp_image(self, image: QImage) -> Optional[str]:
        """一時的な画像ファイルの保存"""
        with self._lock:
            try:
                temp_filename = f"temp_{uuid.uuid4().hex}.png"
                temp_path = os.path.join(self._temp_dir, temp_filename)
                
                if image.save(temp_path, "PNG"):
                    logger.debug(f"一時画像を保存: {temp_path}")
                    return temp_path
                return None

            except Exception as e:
                logger.error(f"一時画像の保存に失敗: {e}")
                return None

    def clear_cache(self) -> None:
        """画像キャッシュのクリア"""
        with self._lock:
            self._image_cache.clear()
            self._current_cache_size = 0
            self._cleanup_temp_files()

    def _add_to_cache(self, image_path: str, image: QImage) -> None:
        """キャッシュへの画像追加"""
        image_size = image.sizeInBytes()

        while (self._current_cache_size + image_size > self._max_cache_size and
               self._image_cache):
            # LRU方式でキャッシュをクリア
            oldest_path = next(iter(self._image_cache))
            oldest_image = self._image_cache.pop(oldest_path)
            self._current_cache_size -= oldest_image.sizeInBytes()

        self._image_cache[image_path] = image
        self._current_cache_size += image_size

    def _cleanup_temp_files(self) -> None:
        """古い一時ファイルの削除"""
        try:
            current_time = time.time()
            for filename in os.listdir(self._temp_dir):
                filepath = os.path.join(self._temp_dir, filename)
                if not filename.startswith("temp_"):
                    continue

                file_time = os.path.getctime(filepath)
                if current_time - file_time > 3600:  # 1時間以上経過
                    os.remove(filepath)

        except Exception as e:
            logger.error(f"一時ファイルのクリーンアップに失敗: {e}")

    def _is_supported_format(self, filepath: str) -> bool:
        """サポートされている画像形式かチェック"""
        return os.path.splitext(filepath)[1].lower() in self._supported_formats
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import time
import uuid
import threading
from typing import Optional, Dict
from PySide6.QtGui import QImage
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 画像の読み込み
1. キャッシュチェック
2. ファイル存在確認
3. 形式の検証
4. 画像データの読み込み
5. キャッシュへの保存

### 4.2 一時ファイル管理
1. 一時ファイル名の生成
2. ファイルの保存
3. パス情報の管理
4. 有効期限の制御
5. 自動クリーンアップ

### 4.3 キャッシュ管理
1. メモリ使用量の監視
2. LRU方式による削除
3. キャッシュサイズの制御
4. 整合性の維持
5. パフォーマンスの最適化

## 5. エラー処理

### 5.1 想定されるエラー
- ファイルが存在しない
- 未対応の画像形式
- 破損した画像データ
- メモリ不足
- ディスク容量不足

### 5.2 エラー処理方針
- ファイル不在 → Noneを返却
- 未対応形式 → エラーログを記録
- データ破損 → 読み込み失敗を通知
- メモリ不足 → キャッシュをクリア
- ディスク不足 → 一時ファイルを削除

## 6. スレッド安全性

### 6.1 排他制御
- キャッシュアクセスのロック
- ファイル操作の保護
- 一時ファイル管理の同期

### 6.2 同時アクセス制御
- 読み取り優先度の設定
- 書き込み操作の直列化
- デッドロック防止

## 7. パフォーマンス考慮事項

### 7.1 キャッシュ管理
- メモリ使用量の監視
- キャッシュサイズの最適化
- 効率的なLRU実装

### 7.2 ファイルI/O
- 非同期読み込みの検討
- バッファリングの活用
- 一時ファイルの効率的な管理

## 8. 画像形式サポート

### 8.1 対応フォーマット
- PNG (.png)
- JPEG (.jpg, .jpeg)
- BMP (.bmp)
- GIF (.gif)

### 8.2 制約事項
- アニメーションGIFは最初のフレームのみ
- 最大ファイルサイズ制限
- 画像サイズの制限
- カラーモードの制限
