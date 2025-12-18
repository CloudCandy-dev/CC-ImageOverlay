# MonitorService 詳細設計

## 1. 概要
モニター情報の取得と管理を担当するサービスクラス。複数モニター環境での表示位置の制御、モニター間の移動制限、プライマリモニターの管理などを行う。

## 2. クラス定義

```python
class MonitorService:
    """モニター管理サービスクラス"""
    
    def __init__(self):
        self._monitors = []
        self._primary_monitor = None
        self._current_monitor = None
        self._app = QApplication.instance()

    @property
    def monitors(self) -> list[Monitor]:
        """利用可能なモニターのリストを取得"""
        return self._monitors.copy()

    @property
    def primary_monitor(self) -> Monitor:
        """プライマリモニターを取得"""
        return self._primary_monitor

    @property
    def current_monitor(self) -> Monitor:
        """現在選択中のモニターを取得"""
        return self._current_monitor

    def initialize(self) -> None:
        """モニター情報の初期化"""
        self._update_monitor_info()
        screen = self._app.primaryScreen()
        self._primary_monitor = Monitor.from_screen(screen)
        self._current_monitor = self._primary_monitor

    def refresh_monitor_info(self) -> None:
        """モニター情報の更新"""
        self._update_monitor_info()

    def set_current_monitor(self, monitor_id: str) -> bool:
        """現在のモニターを設定"""
        monitor = self.find_monitor(monitor_id)
        if monitor:
            self._current_monitor = monitor
            return True
        return False

    def find_monitor(self, monitor_id: str) -> Optional[Monitor]:
        """指定IDのモニターを検索"""
        for monitor in self._monitors:
            if monitor.id == monitor_id:
                return monitor
        return None

    def get_monitor_at(self, x: int, y: int) -> Optional[Monitor]:
        """指定座標にあるモニターを取得"""
        for monitor in self._monitors:
            if monitor.contains_point(x, y):
                return monitor
        return None

    def validate_window_position(self, x: int, y: int, width: int, height: int) -> bool:
        """ウィンドウ位置の妥当性を検証"""
        if not self._current_monitor:
            return False
        return self._current_monitor.contains_rect(x, y, width, height)

    def adjust_position_to_monitor(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        """ウィンドウ位置をモニター内に調整"""
        if not self._current_monitor:
            return x, y

        monitor_rect = self._current_monitor.geometry
        new_x = max(monitor_rect.x(), min(x, monitor_rect.right() - width))
        new_y = max(monitor_rect.y(), min(y, monitor_rect.bottom() - height))
        return new_x, new_y

    def _update_monitor_info(self) -> None:
        """モニター情報を更新"""
        self._monitors.clear()
        for screen in self._app.screens():
            monitor = Monitor.from_screen(screen)
            self._monitors.append(monitor)
        
        # プライマリモニターの更新
        primary_screen = self._app.primaryScreen()
        self._primary_monitor = Monitor.from_screen(primary_screen)

        # 現在のモニターが無効になった場合の処理
        if self._current_monitor:
            monitor_exists = any(
                m.id == self._current_monitor.id
                for m in self._monitors
            )
            if not monitor_exists:
                self._current_monitor = self._primary_monitor
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from typing import Optional
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication
from ..entities.monitor import Monitor
```

## 4. 主要メソッドの処理詳細

### 4.1 初期化処理（initialize）
1. 現在のモニター構成を取得
2. プライマリモニターの特定
3. モニター情報の初期化
4. 現在のモニターをプライマリモニターに設定

### 4.2 モニター情報更新（refresh_monitor_info）
1. モニターリストのクリア
2. 現在のモニター構成を再取得
3. モニター情報の更新
4. 無効になったモニターの処理

### 4.3 位置の検証と調整
1. モニター境界のチェック
2. ウィンドウサイズの考慮
3. 必要に応じた位置の補正
4. 新しい座標の計算

## 5. モニター管理

### 5.1 モニター情報
- モニターID
- 物理的な位置
- 解像度
- スケーリング
- プライマリフラグ

### 5.2 モニター間の制約
- モニター間の移動不可
- 各モニター内での移動のみ許可
- プライマリモニターへのフォールバック

## 6. エラー処理

### 6.1 想定されるエラー
- モニター構成の変更
- 無効なモニターID
- 範囲外の座標指定
- Qt APIエラー

### 6.2 エラー処理方針
- モニター切断 → プライマリモニターに切り替え
- 無効なID → プライマリモニターを使用
- 範囲外座標 → 有効範囲内に補正
- API失敗 → エラーログを記録

## 7. パフォーマンス考慮事項

### 7.1 最適化
- モニター情報のキャッシュ
- 不要な更新の抑制
- 座標計算の効率化

### 7.2 メモリ管理
- モニターリストの適切な管理
- 古い情報の適切なクリーンアップ
- リソースの効率的な使用

## 8. 将来の拡張性

### 8.1 対応予定の機能
- モニター追加/削除イベントの通知
- より詳細なモニター情報の提供
- モニター固有の設定管理

### 8.2 制約事項
- Windows環境のみ対応
- Qt依存のモニター情報取得
- マルチディスプレイ制限
