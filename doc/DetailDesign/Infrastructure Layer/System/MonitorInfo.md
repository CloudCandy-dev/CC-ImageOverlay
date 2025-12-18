# MonitorInfo 詳細設計

## 1. 概要
システムのマルチモニター情報を取得し、モニターの配置、解像度、スケーリング情報を管理するクラス。Windows APIを利用してモニター情報へアクセスする。

## 2. クラス定義

```python
class MonitorInfo:
    """モニター情報管理クラス"""
    
    def __init__(self):
        self._monitors = []
        self._primary_monitor = None
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        """モニター情報システムの初期化"""
        try:
            self.refresh_monitor_info()
            return True
        except Exception as e:
            logger.error(f"モニター情報システムの初期化に失敗: {e}")
            return False

    def refresh_monitor_info(self) -> None:
        """モニター情報の更新"""
        with self._lock:
            try:
                monitors = []
                def enum_monitor(hmonitor: int, hdc: int, rect: win32gui.RECT, data: int) -> int:
                    info = win32gui.GetMonitorInfo(hmonitor)
                    monitor = {
                        'handle': hmonitor,
                        'device': info['Device'],
                        'rect': rect,
                        'work_rect': info['Work'],
                        'is_primary': info['Flags'] & win32con.MONITORINFOF_PRIMARY
                    }
                    monitors.append(monitor)
                    return True

                win32gui.EnumDisplayMonitors(None, None, enum_monitor, 0)
                self._monitors = monitors
                self._update_primary_monitor()
                logger.debug(f"モニター情報を更新: {len(self._monitors)}台検出")

            except Exception as e:
                logger.error(f"モニター情報の更新に失敗: {e}")
                self._monitors = []
                self._primary_monitor = None

    def get_monitor_count(self) -> int:
        """接続されているモニターの数を取得"""
        return len(self._monitors)

    def get_monitor_list(self) -> List[Dict]:
        """全モニターの情報を取得"""
        return self._monitors.copy()

    def get_primary_monitor(self) -> Optional[Dict]:
        """プライマリモニターの情報を取得"""
        return self._primary_monitor

    def get_monitor_at_point(self, x: int, y: int) -> Optional[Dict]:
        """指定座標にあるモニターを取得"""
        for monitor in self._monitors:
            rect = monitor['rect']
            if (rect.left <= x <= rect.right and
                rect.top <= y <= rect.bottom):
                return monitor
        return None

    def get_monitor_by_handle(self, handle: int) -> Optional[Dict]:
        """ハンドルからモニター情報を取得"""
        for monitor in self._monitors:
            if monitor['handle'] == handle:
                return monitor
        return None

    def get_monitor_dpi(self, handle: int) -> Tuple[int, int]:
        """モニターのDPI情報を取得"""
        try:
            dpiX = ctypes.c_uint()
            dpiY = ctypes.c_uint()
            shcore.GetDpiForMonitor(
                handle,
                win32con.MDT_EFFECTIVE_DPI,
                ctypes.byref(dpiX),
                ctypes.byref(dpiY)
            )
            return dpiX.value, dpiY.value
        except Exception as e:
            logger.error(f"DPI情報の取得に失敗: {e}")
            return 96, 96  # デフォルトDPI

    def get_monitor_scaling(self, handle: int) -> float:
        """モニターのスケーリング率を取得"""
        try:
            dpiX, _ = self.get_monitor_dpi(handle)
            return dpiX / 96.0
        except Exception:
            return 1.0  # デフォルトスケーリング

    def _update_primary_monitor(self) -> None:
        """プライマリモニター情報の更新"""
        for monitor in self._monitors:
            if monitor['is_primary']:
                self._primary_monitor = monitor
                break
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import win32gui
import win32con
import ctypes
import threading
from typing import Dict, List, Optional, Tuple
from ctypes import windll
from ..services.logging_service import logger

# DPI認識の初期化
shcore = ctypes.WinDLL('shcore')
windll.user32.SetProcessDPIAware()
```

## 4. 主要機能の詳細

### 4.1 モニター列挙
1. システムAPI呼び出し
2. モニター情報の収集
3. プライマリ判定
4. データ構造の構築
5. エラーハンドリング

### 4.2 モニター情報取得
1. 位置情報の解析
2. DPI情報の取得
3. スケーリングの計算
4. 作業領域の確認
5. デバイス情報の収集

### 4.3 座標変換
1. 物理座標の変換
2. 論理座標の計算
3. DPIスケーリング
4. モニター境界の処理
5. オーバーフロー対策

## 5. エラー処理

### 5.1 想定されるエラー
- API呼び出し失敗
- モニター接続変更
- DPI取得エラー
- メモリ不足
- 権限不足

### 5.2 エラー処理方針
- API失敗 → デフォルト値を使用
- 接続変更 → 再列挙を実行
- DPIエラー → 標準DPIを使用
- メモリ不足 → キャッシュをクリア
- 権限エラー → エラーログを記録

## 6. スレッド安全性

### 6.1 排他制御
- モニター情報の更新ロック
- DPI情報のキャッシュ
- 座標変換の保護

### 6.2 同時アクセス制御
- 読み取り優先度の設定
- 更新操作の直列化
- デッドロック防止

## 7. パフォーマンス考慮事項

### 7.1 キャッシュ管理
- モニター情報のキャッシュ
- DPI値のキャッシュ
- 更新頻度の最適化

### 7.2 リソース管理
- APIハンドルの管理
- メモリ使用量の制御
- システムリソースの解放

## 8. プラットフォーム依存性

### 8.1 Windows固有の実装
- Win32 APIの使用
- DPI認識モード
- モニターAPI制約

### 8.2 制約事項
- Windows環境のみ対応
- DPIの変更検知制限
- モニター数の制限
- API互換性要件
