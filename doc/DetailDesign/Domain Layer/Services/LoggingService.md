# LoggingService 詳細設計

## 1. 概要
アプリケーション全体のログ管理を担当するサービスクラス。ログの出力、ローテーション、フォーマット管理を行う。

## 2. クラス定義

```python
class LoggingService:
    """ログ管理サービスクラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self._config_manager = config_manager
        self._log_dir = "logs"
        self._max_log_files = 5
        self._current_log_file = None
        self._formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def initialize(self) -> None:
        """ログサービスの初期化"""
        self._setup_log_directory()
        self._setup_logging()
        self._rotate_logs()

    def log_error(self, message: str, exc_info: Exception = None) -> None:
        """エラーログを記録"""
        logging.error(message, exc_info=exc_info)

    def log_warning(self, message: str) -> None:
        """警告ログを記録"""
        logging.warning(message)

    def log_info(self, message: str) -> None:
        """情報ログを記録"""
        logging.info(message)

    def log_debug(self, message: str) -> None:
        """デバッグログを記録"""
        logging.debug(message)

    def _setup_log_directory(self) -> None:
        """ログディレクトリの準備"""
        if not os.path.exists(self._log_dir):
            os.makedirs(self._log_dir)

    def _setup_logging(self) -> None:
        """ロギングの設定"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"cc_image_overlay_{timestamp}.log"
        self._current_log_file = os.path.join(self._log_dir, log_file)

        file_handler = RotatingFileHandler(
            self._current_log_file,
            maxBytes=1024 * 1024,  # 1MB
            backupCount=1
        )
        file_handler.setFormatter(self._formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self._formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def _rotate_logs(self) -> None:
        """古いログファイルの管理"""
        log_files = glob.glob(os.path.join(self._log_dir, "cc_image_overlay_*.log"))
        if len(log_files) > self._max_log_files:
            log_files.sort()
            for old_file in log_files[:-self._max_log_files]:
                try:
                    os.remove(old_file)
                except OSError as e:
                    print(f"ログファイルの削除に失敗: {e}")

    def get_recent_logs(self, num_lines: int = 100) -> list[str]:
        """最新のログエントリを取得"""
        if not self._current_log_file or not os.path.exists(self._current_log_file):
            return []

        try:
            with open(self._current_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return lines[-num_lines:]
        except Exception as e:
            print(f"ログの読み込みに失敗: {e}")
            return []
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import glob
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from .config_manager import ConfigManager
```

## 4. 主要メソッドの処理詳細

### 4.1 初期化処理（initialize）
1. ログディレクトリの存在確認と作成
2. ログファイルの設定
   - タイムスタンプベースのファイル名生成
   - ファイルハンドラの設定
   - コンソールハンドラの設定
3. 古いログファイルのローテーション

### 4.2 ログレベル別の処理
- ERROR: クリティカルなエラー（例外情報付き）
- WARNING: 警告メッセージ
- INFO: 操作履歴、状態変更
- DEBUG: 詳細なデバッグ情報

### 4.3 ログローテーション（_rotate_logs）
1. ログディレクトリ内のファイル一覧取得
2. タイムスタンプによるソート
3. 最大数を超えた古いファイルの削除

## 5. ログフォーマット

### 5.1 基本フォーマット
```
YYYY-MM-DD HH:MM:SS [LEVEL] Message
```

### 5.2 エラーログフォーマット
```
YYYY-MM-DD HH:MM:SS [ERROR] Message
Traceback (most recent call last):
  ...
Exception details
```

## 6. エラー処理

### 6.1 想定されるエラー
- ディレクトリ作成失敗
- ファイル書き込み権限なし
- ディスク容量不足
- ファイル削除失敗

### 6.2 エラー処理方針
- ディレクトリエラー → 標準出力に警告
- 書き込みエラー → 標準出力にフォールバック
- 容量エラー → 古いログの強制削除
- 削除エラー → 警告を出力して継続

## 7. パフォーマンス考慮事項

### 7.1 ファイル管理
- ログファイルサイズの制限（1MB）
- 保持するログファイル数の制限（5件）
- 定期的なローテーション

### 7.2 書き込みパフォーマンス
- バッファリングの活用
- 非同期書き込みの検討
- ログレベルによるフィルタリング
