# ConfigStorage 詳細設計

## 1. 概要
アプリケーションの設定をJSONファイルとして永続化するクラス。ファイルの読み書き、バックアップ、検証を担当する。

## 2. クラス定義

```python
class ConfigStorage:
    """設定ファイルの永続化を管理するクラス"""
    
    def __init__(self, config_path: str = "configs/config.json"):
        self._config_path = config_path
        self._backup_path = f"{config_path}.backup"
        self._lock = threading.Lock()

    def load(self) -> dict:
        """設定をファイルから読み込み"""
        with self._lock:
            try:
                return self._load_config()
            except Exception as e:
                logger.error(f"設定の読み込みに失敗: {e}")
                if os.path.exists(self._backup_path):
                    return self._load_backup()
                return {}

    def save(self, config: dict) -> bool:
        """設定をファイルに保存"""
        with self._lock:
            try:
                self._backup_current()
                return self._save_config(config)
            except Exception as e:
                logger.error(f"設定の保存に失敗: {e}")
                return False

    def _load_config(self) -> dict:
        """設定ファイルを読み込み"""
        if not os.path.exists(self._config_path):
            return {}

        with open(self._config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if self._validate_config(data):
                return data
            raise ValueError("無効な設定データ")

    def _save_config(self, config: dict) -> bool:
        """設定をファイルに書き込み"""
        if not self._validate_config(config):
            return False

        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True

    def _backup_current(self) -> None:
        """現在の設定ファイルをバックアップ"""
        if os.path.exists(self._config_path):
            shutil.copy2(self._config_path, self._backup_path)

    def _load_backup(self) -> dict:
        """バックアップから設定を読み込み"""
        try:
            with open(self._backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if self._validate_config(data):
                    return data
        except Exception as e:
            logger.error(f"バックアップの読み込みに失敗: {e}")
        return {}

    def _validate_config(self, config: dict) -> bool:
        """設定データの検証"""
        try:
            required_keys = {
                "app_settings",
                "overlay_settings",
                "hotkey_settings"
            }
            if not all(key in config for key in required_keys):
                return False

            # app_settings の検証
            app_settings = config["app_settings"]
            if not all(key in app_settings for key in [
                "window", "language", "theme", "last_image_path"
            ]):
                return False

            # overlay_settings の検証
            overlay_settings = config["overlay_settings"]
            if not all(key in overlay_settings for key in [
                "position", "size", "opacity", "rotation", "monitor"
            ]):
                return False

            # hotkey_settings の検証
            hotkey_settings = config["hotkey_settings"]
            if not all(key in hotkey_settings for key in ["toggle_overlay"]):
                return False

            return True
        except Exception:
            return False
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import json
import shutil
import threading
from typing import Optional
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 設定の読み込み処理
1. ファイルの存在確認
2. JSONデータの読み込み
3. データの検証
4. エラー時のバックアップ使用
5. デフォルト値の提供

### 4.2 設定の保存処理
1. 現在の設定のバックアップ
2. データの検証
3. ディレクトリの作成確認
4. JSONフォーマットでの書き込み
5. エラー処理とリカバリ

### 4.3 データの検証処理
1. 必須キーの存在確認
2. データ型の検証
3. 値の範囲チェック
4. 整合性の確認

## 5. エラー処理

### 5.1 想定されるエラー
- ファイルが存在しない
- ファイルの読み書き権限がない
- JSONフォーマットが不正
- 必須項目の欠落
- ディスク容量不足

### 5.2 エラー処理方針
- ファイル不在 → 空の設定を返却
- パース失敗 → バックアップを使用
- 権限エラー → エラーログを記録
- 検証失敗 → デフォルト値を使用
- 書き込み失敗 → 元の設定を維持

## 6. スレッド安全性

### 6.1 排他制御
- ファイルアクセスのロック
- 設定データの整合性保護
- 複数の書き込み要求の順序保証

### 6.2 同時アクセス制御
- 読み込み処理の優先
- 書き込みのキューイング
- デッドロック防止

## 7. パフォーマンス考慮事項

### 7.1 ファイルI/O最適化
- 必要な場合のみ書き込み
- バッファリングの活用
- 適切なファイルサイズ管理

### 7.2 メモリ管理
- 大きな設定データの効率的な処理
- 不要なコピーの削減
- リソースの適切な解放

## 8. バックアップと復元

### 8.1 バックアップ戦略
- 設定変更前のバックアップ作成
- 最新のバックアップのみ保持
- バックアップの整合性確認

### 8.2 復元プロセス
- バックアップの検証
- 段階的な復元
- エラー時の対応
