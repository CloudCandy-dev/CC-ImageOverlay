# イベント定義 詳細設計

## 1. 概要
アプリケーション全体で使用される共通イベントの定義。レイヤー間の通信と状態同期を標準化します。

## 2. イベント定義

### 2.1 UIイベント
```python
class UIEvent:
    """UI関連イベントの基底クラス"""
    event_id: str
    timestamp: datetime
    source: str

class WindowStateEvent(UIEvent):
    """ウィンドウ状態変更イベント"""
    geometry: QRect
    is_maximized: bool
    is_visible: bool

class OverlayStateEvent(UIEvent):
    """オーバーレイ状態変更イベント"""
    geometry: QRect
    opacity: float
    is_visible: bool
    monitor_id: str
```

### 2.2 設定イベント
```python
class SettingsEvent:
    """設定関連イベントの基底クラス"""
    setting_key: str
    old_value: Any
    new_value: Any
    auto_apply: bool

class ThemeChangedEvent(SettingsEvent):
    """テーマ変更イベント"""
    theme_name: str
    stylesheet: str

class LanguageChangedEvent(SettingsEvent):
    """言語変更イベント"""
    language_code: str
    translations: Dict[str, str]
```

### 2.3 エラーイベント
```python
class ErrorEvent:
    """エラーイベントの基底クラス"""
    error_code: str
    message: str
    details: Optional[Dict]
    timestamp: datetime
    severity: ErrorSeverity

class ValidationErrorEvent(ErrorEvent):
    """バリデーションエラーイベント"""
    field_errors: Dict[str, List[str]]
    entity_type: str

class SystemErrorEvent(ErrorEvent):
    """システムエラーイベント"""
    stack_trace: str
    recoverable: bool
```

## 3. イベントハンドリング

### 3.1 イベントバス
```python
class EventBus:
    """アプリケーション全体のイベントバス"""
    
    @staticmethod
    def subscribe(event_type: Type[UIEvent], handler: Callable[[UIEvent], None]) -> None:
        """イベントハンドラーの登録"""
        pass
    
    @staticmethod
    async def publish(event: UIEvent) -> None:
        """イベントの発行"""
        pass
    
    @staticmethod
    def unsubscribe(event_type: Type[UIEvent], handler: Callable[[UIEvent], None]) -> None:
        """イベントハンドラーの解除"""
        pass
```

### 3.2 イベントフィルタリング
```python
class EventFilter:
    """イベントフィルタリング機能"""
    
    def __init__(self, event_type: Type[UIEvent], condition: Callable[[UIEvent], bool]):
        self.event_type = event_type
        self.condition = condition
    
    def apply(self, event: UIEvent) -> bool:
        """フィルタの適用"""
        return isinstance(event, self.event_type) and self.condition(event)
```

## 4. イベント伝播

### 4.1 伝播ルール
1. UIイベント：
   - View → ViewModel → Model（上位レイヤーへの伝播）
   - エラー時は即座に下位レイヤーへ通知

2. 設定イベント：
   - Model → ViewModel → View（下位レイヤーへの伝播）
   - 即時適用が必要な設定は直接Viewへ通知

3. エラーイベント：
   - 発生場所から即座に関連コンポーネントへ通知
   - クリティカルエラーはアプリケーション全体に通知

### 4.2 伝播制御
```python
class EventPropagationController:
    """イベント伝播の制御"""
    
    @staticmethod
    def should_propagate(event: UIEvent, target_layer: str) -> bool:
        """伝播判定"""
        pass
    
    @staticmethod
    def get_propagation_path(event: UIEvent) -> List[str]:
        """伝播パスの取得"""
        pass
```

## 5. エラー処理

### 5.1 イベントエラー処理
```python
class EventError(Exception):
    """イベント処理エラー"""
    def __init__(self, message: str, event: UIEvent, error_code: str):
        super().__init__(message)
        self.event = event
        self.error_code = error_code

class EventErrorHandler:
    """イベントエラーハンドラー"""
    
    @staticmethod
    async def handle_error(error: EventError) -> None:
        """エラー処理"""
        pass
```
