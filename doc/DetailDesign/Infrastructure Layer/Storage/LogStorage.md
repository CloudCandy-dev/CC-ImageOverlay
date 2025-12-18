# LogStorage 詳細設計

## 1. 概要
アプリケーションのログをファイルシステムに永続化するクラス。ログの書き込み、ローテーション、保持期間管理を担当する。

## 2. クラス定義

```python
class LogStorage:
    """ログファイルの永続化を管理するクラス"""
    
    def __init__(self, log_dir: str = "logs"):
        self._log_dir = log_dir
        self._current_log_file = None
        self._max_log_size = 10 * 1024 * 1024  # 10MB
        self._max_backup_count = 5
        self._retention_days = 30
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        """ログストレージの初期化"""
        try:
            os.makedirs(self._log_dir, exist_ok=True)
            self._current_log_file = self._create_log_file()
            self._cleanup_old_logs()
            return True
        except Exception as e:
            print(f"ログストレージの初期化に失敗: {e}")
            return False

    def write_log(self, level: str, message: str) -> bool:
        """ログメッセージの書き込み"""
        with self._lock:
            try:
                if self._should_rotate():
                    self._rotate_logs()

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"[{timestamp}] [{level}] {message}\n"
                
                with open(self._current_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
                return True
            except Exception as e:
                print(f"ログの書き込みに失敗: {e}")
                return False

    def get_recent_logs(self, lines: int = 100) -> list[str]:
        """最新のログエントリを取得"""
        with self._lock:
            try:
                if not os.path.exists(self._current_log_file):
                    return []

                with open(self._current_log_file, 'r', encoding='utf-8') as f:
                    return self._get_last_n_lines(f, lines)
            except Exception as e:
                print(f"ログの読み込みに失敗: {e}")
                return []

    def _create_log_file(self) -> str:
        """新しいログファイルを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self._log_dir, f"app_{timestamp}.log")

    def _should_rotate(self) -> bool:
        """ログローテーションが必要か判断"""
        try:
            size = os.path.getsize(self._current_log_file)
            return size >= self._max_log_size
        except Exception:
            return False

    def _rotate_logs(self) -> None:
        """ログファイルのローテーション処理"""
        if not os.path.exists(self._current_log_file):
            return

        new_log_file = self._create_log_file()
        for i in range(self._max_backup_count - 1, 0, -1):
            old = f"{self._current_log_file}.{i}"
            new = f"{self._current_log_file}.{i + 1}"
            if os.path.exists(old):
                os.rename(old, new)

        os.rename(self._current_log_file, f"{self._current_log_file}.1")
        self._current_log_file = new_log_file

    def _cleanup_old_logs(self) -> None:
        """古いログファイルの削除"""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self._log_dir):
                filepath = os.path.join(self._log_dir, filename)
                if not filename.startswith("app_") or not filename.endswith(".log"):
                    continue

                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if (current_time - file_time).days > self._retention_days:
                    os.remove(filepath)
        except Exception as e:
            print(f"古いログの削除に失敗: {e}")

    def _get_last_n_lines(self, file, n: int) -> list[str]:
        """ファイルの末尾からn行を取得"""
        lines = []
        try:
            file.seek(0, os.SEEK_END)
            position = file.tell()
            line_count = 0
            
            while position >= 0 and line_count < n:
                file.seek(position)
                if position > 0:
                    file.seek(position - 1)
                char = file.read(1)
                if char == "\n" and position != file.tell() - 1:
                    line = file.readline()
                    lines.append(line.rstrip())
                    line_count += 1
                position -= 1
            
            return list(reversed(lines))
        except Exception:
            return lines
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import threading
from datetime import datetime
from typing import List
```

## 4. 主要機能の詳細

### 4.1 ログの書き込み
1. ログローテーションの確認
2. タイムスタンプの生成
3. ログレベルの付与
4. ファイルへの書き込み
5. 排他制御の実施

### 4.2 ログローテーション
1. サイズ制限の確認
2. バックアップファイルの作成
3. ファイルの名前変更
4. 新規ファイルの作成
5. 古いログの削除

### 4.3 ログファイル管理
1. ディレクトリの作成
2. ファイル名の生成
3. パーミッションの設定
4. 保持期間の管理
5. クリーンアップの実行

## 5. エラー処理

### 5.1 想定されるエラー
- ディスク容量不足
- 書き込み権限なし
- ファイルロック
- I/Oエラー
- ディレクトリ作成失敗

### 5.2 エラー処理方針
- 書き込み失敗 → エラーを標準出力に出力
- 権限エラー → 管理者権限の要求
- ディスク不足 → 古いログの削除
- ロック競合 → リトライ処理
- I/Oエラー → 代替パスの使用

## 6. スレッド安全性

### 6.1 排他制御
- ファイル書き込みのロック
- ローテーション処理の保護
- 読み取り操作の同期

### 6.2 同時アクセス制御
- 書き込みキューの管理
- 読み取り優先度の設定
- デッドロック防止

## 7. パフォーマンス考慮事項

### 7.1 I/O最適化
- バッファリングの活用
- 非同期書き込みの検討
- ファイルディスクリプタの管理

### 7.2 リソース管理
- ファイルハンドルの適切なクローズ
- メモリ使用量の制御
- CPU負荷の最適化

## 8. 設定パラメータ

### 8.1 カスタマイズ可能な項目
- ログディレクトリのパス
- 最大ファイルサイズ
- バックアップ数
- 保持期間
- バッファサイズ

### 8.2 デフォルト値
- ログディレクトリ: "logs"
- 最大ファイルサイズ: 10MB
- バックアップ数: 5
- 保持期間: 30日
- バッファサイズ: 8KB
