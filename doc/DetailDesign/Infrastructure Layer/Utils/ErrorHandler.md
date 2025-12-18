# ErrorHandler 詳細設計

## 1. 概要
アプリケーション全体のエラー処理を一元管理するユーティリティクラス。エラーの捕捉、ログ記録、ユーザー通知、リカバリ処理を統一的に提供する。

## 2. クラス定義

```python
class ErrorHandler:
    """エラー処理管理クラス"""
    
    def __init__(self):
        self._error_callbacks = {}
        self._last_error = None
        self._lock = threading.Lock()
        self._error_count = {}
        self._max_retry_count = 3
        self._error_window = None

    @staticmethod
    def handle(error_type: str, exception: Exception, context: dict = None) -> None:
        """エラーの処理を実行"""
        try:
            instance = ErrorHandler()
            instance._process_error(error_type, exception, context)
        except Exception as e:
            logger.critical(f"エラーハンドラでの例外発生: {e}")
            # 最後の手段として標準出力にエラーを出力
            print(f"Critical Error: {e}")

    def register_callback(self, error_type: str, callback: Callable) -> None:
        """エラータイプに対するコールバックを登録"""
        with self._lock:
            if error_type not in self._error_callbacks:
                self._error_callbacks[error_type] = []
            self._error_callbacks[error_type].append(callback)

    def _process_error(self, error_type: str, exception: Exception, context: dict = None) -> None:
        """エラー処理の実行"""
        with self._lock:
            try:
                # エラー情報の記録
                self._last_error = {
                    'type': error_type,
                    'message': str(exception),
                    'timestamp': datetime.now(),
                    'context': context or {}
                }

                # エラー発生回数のカウント
                self._error_count[error_type] = self._error_count.get(error_type, 0) + 1

                # ログへの記録
                self._log_error()

                # 重大度に応じた処理
                if self._is_critical_error(error_type):
                    self._handle_critical_error()
                elif self._can_retry(error_type):
                    self._handle_retryable_error()
                else:
                    self._handle_normal_error()

                # コールバックの実行
                self._execute_callbacks(error_type, exception)

            except Exception as e:
                logger.critical(f"エラー処理中の例外: {e}")

    def _log_error(self) -> None:
        """エラー情報をログに記録"""
        error = self._last_error
        logger.error(
            f"エラー発生: {error['type']}\n"
            f"メッセージ: {error['message']}\n"
            f"コンテキスト: {error['context']}"
        )

    def _handle_critical_error(self) -> None:
        """重大なエラーの処理"""
        error = self._last_error
        # ユーザーへの通知
        self._show_error_dialog(
            "Critical Error",
            f"重大なエラーが発生しました。\n{error['message']}",
            QMessageBox.Critical
        )
        # アプリケーションの状態保存
        self._save_application_state()

    def _handle_retryable_error(self) -> None:
        """リトライ可能なエラーの処理"""
        error = self._last_error
        if self._error_count[error['type']] <= self._max_retry_count:
            # リトライ処理
            self._retry_operation()
        else:
            # リトライ回数超過
            self._handle_retry_exceeded()

    def _handle_normal_error(self) -> None:
        """通常のエラーの処理"""
        error = self._last_error
        # ユーザーへの通知（必要な場合）
        if self._should_notify_user(error['type']):
            self._show_error_dialog(
                "Error",
                error['message'],
                QMessageBox.Warning
            )

    def _is_critical_error(self, error_type: str) -> bool:
        """重大なエラーかどうかを判定"""
        critical_types = {
            'SystemError',
            'MemoryError',
            'WindowsError'
        }
        return error_type in critical_types

    def _can_retry(self, error_type: str) -> bool:
        """リトライ可能なエラーかどうかを判定"""
        retryable_types = {
            'NetworkError',
            'TimeoutError',
            'IOError'
        }
        return error_type in retryable_types

    def _should_notify_user(self, error_type: str) -> bool:
        """ユーザーに通知すべきエラーかどうかを判定"""
        notify_types = {
            'ValidationError',
            'ConfigError',
            'UserInputError'
        }
        return error_type in notify_types

    def _show_error_dialog(self, title: str, message: str, icon: int) -> None:
        """エラーダイアログの表示"""
        if QApplication.instance():
            QMessageBox.critical(None, title, message, icon)

    def _execute_callbacks(self, error_type: str, exception: Exception) -> None:
        """登録されたコールバックの実行"""
        callbacks = self._error_callbacks.get(error_type, [])
        for callback in callbacks:
            try:
                callback(error_type, exception)
            except Exception as e:
                logger.error(f"エラーコールバックの実行に失敗: {e}")

    def _save_application_state(self) -> None:
        """アプリケーションの状態を保存"""
        try:
            # クリティカルエラー時の状態保存
            pass
        except Exception as e:
            logger.error(f"アプリケーション状態の保存に失敗: {e}")

    def _retry_operation(self) -> None:
        """操作のリトライ"""
        pass  # 具体的なリトライ処理は呼び出し側で実装
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import threading
from datetime import datetime
from typing import Dict, List, Callable
from PySide6.QtWidgets import QApplication, QMessageBox
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 エラー処理フロー
1. エラー情報の捕捉
2. 重大度の判定
3. ログ記録
4. ユーザー通知
5. リカバリ処理

### 4.2 エラー種別の管理
1. エラータイプの分類
2. 重大度レベルの定義
3. リトライ可能性の判定
4. 通知要否の決定
5. コールバックの実行

### 4.3 リカバリ処理
1. 状態の保存
2. リトライ処理
3. フォールバック
4. クリーンアップ
5. 再初期化

## 5. エラー分類

### 5.1 重大なエラー
- システムエラー
- メモリエラー
- Windowsエラー
- 初期化エラー
- データ破損

### 5.2 リトライ可能なエラー
- ネットワークエラー
- タイムアウト
- I/Oエラー
- 一時的な障害
- リソース競合

### 5.3 通知必要なエラー
- 入力エラー
- 設定エラー
- 検証エラー
- 権限エラー
- 操作エラー

## 6. スレッド安全性

### 6.1 排他制御
- エラー情報のロック
- カウンター管理の保護
- コールバック実行の同期

### 6.2 同時処理
- 並行エラー処理
- コールバックの非同期実行
- UI更新の安全性確保

## 7. パフォーマンス考慮事項

### 7.1 エラー処理の最適化
- 軽量な処理の優先
- メモリ使用量の制御
- スタックトレースの制限

### 7.2 リソース管理
- ログファイルのサイズ管理
- メモリリーク防止
- ファイルハンドルの解放

## 8. デバッグサポート

### 8.1 デバッグ機能
- 詳細ログの出力
- スタックトレースの保存
- エラー統計の収集
- 再現情報の記録

### 8.2 開発者支援
- エラー分析ツール
- トラブルシューティングガイド
- デバッグログの提供
- エラーレポートの生成
