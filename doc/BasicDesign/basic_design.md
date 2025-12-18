# CC-ImageOverlay 基本設計書

## 1. アーキテクチャ設計

### 1.1 全体アーキテクチャ
- MVVMパターンを採用
- 各レイヤーの責務を明確に分離
- 依存性注入を活用した疎結合な設計

### 1.2 レイヤー構造
```
UI Layer (View)
├── MainWindow
├── OverlayWindow
└── Widgets
    ├── PreviewWidget
    └── CustomControls

Presentation Layer (ViewModel)
├── MainWindowViewModel
├── OverlayViewModel
└── Settings
    ├── SettingsBase
    │   ├── loadSettings()
    │   ├── saveSettings()
    │   └── applySettings()
    ├── ThemeManager
    └── LanguageManager

Domain Layer (Model)
├── Core
│   ├── OverlayManager
│   ├── ImageProcessor
│   └── ConfigManager
├── Services
│   ├── HotkeyService
│   ├── MonitorService
│   └── LoggingService
└── Entities
    ├── OverlaySettings
    ├── ApplicationSettings
    └── ImageSettings

Infrastructure Layer
├── Storage
│   ├── ConfigStorage
│   └── LogStorage
├── System
│   ├── GlobalHotkey
│   └── MonitorInfo
└── Utils
    ├── ImageUtils
    └── ErrorHandler
```

### 1.3 モジュール間の依存関係
```
UI Layer → Presentation Layer → Domain Layer → Infrastructure Layer
                                     ↑
                              External Services
```

## 2. モジュール設計

### 2.1 View Layer
- MainWindow
  - メインウィンドウのUI実装
  - ユーザー入力の処理
  - ViewModelとのデータバインディング

- OverlayWindow
  - オーバーレイウィンドウの実装
  - 画像/メモの表示処理
  - ドラッグ＆ドロップ処理

### 2.2 ViewModel Layer
- ViewModelBase
  - プロパティ変更通知の基本実装
  - モデル更新のハンドリング
  - 状態管理の共通機能

- MainWindowViewModel
  - UI状態の管理
    ```json
    {
      "isLoading": "boolean",
      "currentView": "string",
      "selectedImage": "string",
      "errorMessage": "string"
    }
    ```
  - ユーザー操作のロジック
  - ModelとViewの橋渡し
  - ConfigManagerとの連携
    - 設定の読み込み/保存
    - 設定変更の通知

- OverlayViewModel
  - オーバーレイの状態管理
    ```json
    {
      "isVisible": "boolean",
      "position": {"x": "number", "y": "number"},
      "size": {"width": "number", "height": "number"},
      "opacity": "number"
    }
    ```
  - 表示位置やサイズの計算
    - マルチモニター対応の座標変換
    - 境界値チェック
  - 画像処理の制御
    - ImageProcessorとの連携
    - 非同期処理の管理

### 2.3 Model Layer (Domain Layer)

#### 2.3.1 Core

##### 共通型定義
```python
class Result[T]:
    """処理結果を表す共通型"""
    success: bool
    data: Optional[T]
    error: Optional[str]
    error_code: Optional[str]

class ValidationResult:
    """バリデーション結果"""
    is_valid: bool
    errors: Dict[str, List[str]]  # フィールド名とエラーメッセージのマップ
    warnings: Dict[str, List[str]]  # フィールド名と警告メッセージのマップ
```

##### ドメインイベント
```python
class DomainEvent:
    """ドメインイベントの基底クラス"""
    event_id: str
    timestamp: datetime
    source: str

class OverlayStateChanged(DomainEvent):
    """オーバーレイの状態変更イベント"""
    overlay_id: str
    old_state: OverlayState
    new_state: OverlayState

class ConfigurationChanged(DomainEvent):
    """設定変更イベント"""
    setting_key: str
    old_value: Any
    new_value: Any
```

##### Core実装
- DomainModelBase
  ```python
  class DomainModelBase:
      """ドメインモデルの基底クラス"""
      def raise_event(self, event: DomainEvent) -> None
      def validate(self) -> ValidationResult
      def handle_error(self, error: Exception) -> Result
  ```

- OverlayManager
  ```python
  class OverlayManager(DomainModelBase):
      def create_overlay(self, settings: OverlaySettings) -> Result[str]:
          """オーバーレイの作成
          Returns:
              Result[str]: 成功時はオーバーレイIDを返す
          """
      
      def update_overlay(self, overlay_id: str, settings: OverlaySettings) -> Result[None]:
          """オーバーレイの更新"""
      
      def delete_overlay(self, overlay_id: str) -> Result[None]:
          """オーバーレイの削除"""
      
      def get_overlay_state(self, overlay_id: str) -> Result[OverlayState]:
          """オーバーレイの状態取得"""
  ```

- ImageProcessor
  ```python
  class ImageProcessor(DomainModelBase):
      def process_image(self, image: Image, settings: ImageSettings) -> Result[Image]:
          """画像の処理
          Returns:
              Result[Image]: 処理された画像
          """
      
      def validate_image(self, image: Image) -> ValidationResult:
          """画像のバリデーション
          Returns:
              ValidationResult: 検証結果と詳細なエラー情報
          """
      
      def optimize_image(self, image: Image) -> Result[Image]:
          """画像の最適化
          Returns:
              Result[Image]: 最適化された画像
          """
  ```

- ConfigManager
  ```python
  class ConfigManager(DomainModelBase):
      def load_config(self) -> Result[ApplicationSettings]:
          """設定の読み込み"""
      
      def save_config(self, settings: ApplicationSettings) -> Result[None]:
          """設定の保存"""
      
      def validate_config(self, settings: ApplicationSettings) -> ValidationResult:
          """設定のバリデーション"""
      
      def apply_config(self, settings: ApplicationSettings) -> Result[None]:
          """設定の適用"""
      
      def on_config_changed(self, handler: Callable[[ConfigurationChanged], None]) -> None:
          """設定変更イベントのハンドラー登録"""
  ```

#### 2.3.2 Services

##### サービス共通
```python
class ServiceResult[T]:
    """サービス処理結果"""
    success: bool
    data: Optional[T]
    error: Optional[ServiceError]

class ServiceError:
    """サービスエラー情報"""
    code: str
    message: str
    details: Optional[Dict]
    retry_possible: bool
```

- ServiceBase
  ```python
  class ServiceBase:
      """サービスの基底クラス"""
      def begin_transaction(self) -> None
      def commit_transaction(self) -> None
      def rollback_transaction(self) -> None
      
      async def execute_async[T](self, operation: Callable[[], Awaitable[T]]) -> ServiceResult[T]
      def handle_error(self, error: Exception) -> ServiceError
  ```

- HotkeyService
  ```python
  class HotkeyService(ServiceBase):
      def register_hotkey(self, key: str, modifiers: List[str]) -> ServiceResult[None]:
          """ホットキーの登録"""
      
      def unregister_hotkey(self, key: str) -> ServiceResult[None]:
          """ホットキーの解除"""
      
      def handle_hotkey(self, key: str, callback: Callable) -> ServiceResult[None]:
          """ホットキーハンドラーの設定"""
      
      async def wait_for_hotkey(self, key: str) -> ServiceResult[HotkeyEvent]:
          """ホットキーイベントの待機（非同期）"""
  ```

- MonitorService
  ```python
  class MonitorService(ServiceBase):
      async def get_monitor_info(self) -> ServiceResult[List[MonitorInfo]]:
          """モニター情報の取得"""
      
      def get_primary_monitor(self) -> ServiceResult[MonitorInfo]:
          """プライマリーモニターの取得"""
      
      def validate_position(self, position: Position, monitor: str) -> ValidationResult:
          """位置のバリデーション"""
      
      def subscribe_monitor_changes(self, callback: Callable[[MonitorChangeEvent], None]) -> None:
          """モニター変更の監視"""
  ```

- LoggingService
  ```python
  class LoggingService(ServiceBase):
      def log_error(self, error: ServiceError, context: Dict) -> None:
          """エラーログの記録"""
      
      def log_warning(self, message: str, context: Dict, tags: List[str] = None) -> None:
          """警告ログの記録"""
      
      def log_info(self, message: str, context: Dict, tags: List[str] = None) -> None:
          """情報ログの記録"""
      
      async def flush_logs(self) -> ServiceResult[None]:
          """ログの永続化"""
  ```

#### 2.3.3 Entities
- EntityBase
  - ID生成
  - 状態変更通知
  - バリデーション

- OverlaySettings
  ```python
  class OverlaySettings(EntityBase):
      id: str
      position: Position
      size: Size
      opacity: float
      rotation: float
      monitor: str

      def validate(self) -> ValidationResult
      def apply_changes(self, changes: Dict) -> bool
  ```

- ApplicationSettings
  ```python
  class ApplicationSettings(EntityBase):
      window_settings: WindowSettings
      language: str
      theme: str
      last_image_path: str

      def validate(self) -> ValidationResult
      def apply_changes(self, changes: Dict) -> bool
  ```

- ImageSettings
  ```python
  class ImageSettings(EntityBase):
      format: str
      resize_algorithm: str
      quality: int
      optimization_level: int

      def validate(self) -> ValidationResult
      def apply_changes(self, changes: Dict) -> bool
  ```

## 2.4 Infrastructure Layer

### 2.4.1 Storage

#### 共通インターフェース
```python
class StorageBase:
    """ストレージ操作の基底クラス"""
    async def read(self, path: str) -> Result[bytes]
    async def write(self, path: str, data: bytes) -> Result[None]
    async def delete(self, path: str) -> Result[None]
    async def exists(self, path: str) -> bool
    def watch(self, path: str, callback: Callable[[FileSystemEvent], None]) -> None
```

#### ConfigStorage
```python
class ConfigStorage(StorageBase):
    """設定ファイルの永続化管理"""
    async def load_config(self) -> Result[Dict]:
        """設定ファイルの読み込み"""
    
    async def save_config(self, config: Dict) -> Result[None]:
        """設定ファイルの保存"""
    
    async def backup_config(self) -> Result[str]:
        """設定ファイルのバックアップ"""
    
    def watch_config_changes(self, callback: Callable[[ConfigChangeEvent], None]) -> None:
        """設定ファイルの変更監視"""
```

#### LogStorage
```python
class LogStorage(StorageBase):
    """ログファイルの管理"""
    async def write_log(self, level: str, message: str, context: Dict) -> Result[None]:
        """ログの書き込み"""
    
    async def rotate_logs(self) -> Result[None]:
        """ログローテーション"""
    
    async def cleanup_old_logs(self, max_files: int) -> Result[None]:
        """古いログファイルの削除"""
```

### 2.4.2 System

#### グローバルホットキー
```python
class GlobalHotkey:
    """システムレベルのホットキー管理"""
    def register(self, key: str, modifiers: List[str]) -> Result[None]:
        """ホットキーの登録"""
    
    def unregister(self, key: str) -> Result[None]:
        """ホットキーの解除"""
    
    def is_registered(self, key: str) -> bool:
        """ホットキーの登録確認"""
    
    def cleanup(self) -> None:
        """すべてのホットキーの解除"""
```

#### モニター情報
```python
class MonitorInfo:
    """モニター情報の管理"""
    def get_monitors(self) -> List[MonitorDetails]:
        """モニター一覧の取得"""
    
    def get_primary_monitor(self) -> MonitorDetails:
        """プライマリーモニターの取得"""
    
    def add_monitor_change_listener(self, callback: Callable[[MonitorChangeEvent], None]) -> None:
        """モニター変更の監視"""
    
    def convert_coordinates(self, point: Point, from_monitor: str, to_monitor: str) -> Point:
        """モニター間の座標変換"""
```

### 2.4.3 Utils

#### 画像ユーティリティ
```python
class ImageUtils:
    """画像処理ユーティリティ"""
    @staticmethod
    async def load_image(path: str) -> Result[Image]:
        """画像の読み込み"""
    
    @staticmethod
    def resize_image(image: Image, size: Size, algorithm: str) -> Result[Image]:
        """画像のリサイズ"""
    
    @staticmethod
    def optimize_image(image: Image, format: str, quality: int) -> Result[Image]:
        """画像の最適化"""
    
    @staticmethod
    def calculate_memory_usage(image: Image) -> int:
        """メモリ使用量の計算"""
```

#### エラーハンドラー
```python
class ErrorHandler:
    """エラー処理ユーティリティ"""
    @staticmethod
    def handle_error(error: Exception, context: Dict) -> None:
        """エラーのハンドリング"""
    
    @staticmethod
    def show_error_dialog(message: str, details: str = None) -> None:
        """エラーダイアログの表示"""
    
    @staticmethod
    async def log_error(error: Exception, context: Dict) -> None:
        """エラーのログ記録"""
    
    @staticmethod
    def is_critical_error(error: Exception) -> bool:
        """クリティカルエラーの判定"""
```

## 3. データ設計

### 3.1 設定ファイル構造
```json
{
  "app_settings": {
    "window": {
      "x": number,
      "y": number,
      "width": number,
      "height": number
    },
    "language": string,  // 現在選択されている言語ファイル名（例: "Japanese.json"）
    "theme": string,     // 現在選択されているテーマファイル名（例: "dark.qss"）
    "last_image_path": string
  },
  "overlay_settings": {
    "position": {
      "x": number,
      "y": number
    },
    "size": number,
    "opacity": number,
    "rotation": number,
    "monitor": string
  },
  "hotkey_settings": {
    "toggle_overlay": {
      "key": string,
      "modifiers": string[]
    }
  }
}
```

### 3.2 ログファイル設計
- ファイル命名規則：`cc_image_overlay_YYYYMMDD_HHMMSS.log`
- 保持するログファイル数：最新5件
- ログレベル：
  - ERROR: クリティカルなエラー
  - WARN: 警告
  - INFO: 操作履歴
  - DEBUG: デバッグ情報

### 3.3 エラー処理フロー
```
1. エラー発生
   ↓
2. ErrorHandler.handle()
   ├── クリティカルエラー
   │   ├── エラーポップアップ表示
   │   ├── OKボタン待機
   │   └── アプリケーション終了
   └── 非クリティカルエラー
       └── ログ出力のみ
```

## 4. 拡張性設計

### 4.1 プラグインインターフェース
```python
class ImageProcessorPlugin:
    """画像処理プラグインの基底クラス"""
    def apply(self, image: QImage) -> QImage:
        """画像処理を実行"""
        pass

    def get_parameters(self) -> dict:
        """パラメータ情報を取得"""
        pass
```

### 4.2 拡張ポイント
- 画像処理フィルタ
  - 色調補正
  - フィルタ効果
  - カスタム変換

### 4.3 プラグイン管理
- プラグインの動的読み込み
- パラメータの永続化
- UIへの統合

## 5. 状態遷移設計

### 5.1 アプリケーション状態
```
初期状態
  ↓
設定読み込み
  ↓
UI初期化
  ↓
[アイドル状態]
  ├── 画像モード ⟷ メモモード
  ├── オーバーレイ表示 ⟷ 非表示
  └── 設定変更
```

### 5.2 オーバーレイ状態
```
非表示
  ↓
表示準備
  ├── 画像読み込み/メモ設定
  ├── 位置・サイズ計算
  └── 表示設定適用
  ↓
表示状態
  ├── 位置変更
  ├── サイズ変更
  └── 回転/透明度変更
```

## 6. エラー処理設計

### 6.1 エラーカテゴリ
- システムエラー
  - メモリ不足
  - ファイルI/Oエラー
- アプリケーションエラー
  - 設定読み込みエラー
  - 画像処理エラー
- 操作エラー
  - 無効な入力
  - 範囲外の値

### 6.2 ログ管理
- LogManager クラス
  - ログローテーション
  - レベル別ログ出力
  - フォーマット管理

### 6.3 エラー通知
- ErrorNotifier クラス
  - ポップアップ表示制御
  - エラーメッセージの多言語化
  - 重複通知の防止

## 7. 言語ファイル設計

### 7.1 言語ファイル構造
```json
{
    "language": {
        "name": "日本語",
        "code": "ja",
        "region": "JP"
    },
    "messages": {
        "error": {
            "critical": {
                "title": "クリティカルエラー",
                "message": "クリティカルエラーが発生しました。アプリケーションを終了します。"
            },
            "warning": "警告が発生しました。",
            "info": "情報メッセージです。"
        },
        "ui": {
            "settings": {
                "title": "設定",
                "language": "言語",
                "theme": "テーマ",
                "opacity": "不透明度",
                "position": "位置"
            },
            "buttons": {
                "ok": "OK",
                "cancel": "キャンセル",
                "apply": "適用"
            }
        }
    }
}
```

### 7.2 言語ファイル管理
- LanguageManager クラス
  - languages/フォルダからの言語ファイルの動的検出
  - 利用可能な言語のメニューバーへの表示
  - 言語切り替え処理
  - デフォルト言語のフォールバック
  - メッセージキーの検証

### 7.3 言語ファイルの検出と表示
1. アプリケーション起動時
   - languages/フォルダ内の*.jsonファイルを検索
   - 各言語ファイルのメタデータを読み込み
   - メニューバーの言語一覧を構築

2. 言語切り替え時
   - 選択された言語ファイルをロード
   - 設定ファイルの language 値を更新
   - UIコンポーネントの再描画

### 7.4 多言語化プロセス
1. アプリケーション起動時
   - languages/フォルダから利用可能な言語ファイルを検出
   - 設定ファイルから最後に使用した言語設定を読み込み
   - 対応する言語ファイルをロード
   - メニューバーの言語一覧を構築
   - UIへの適用

2. 実行時の言語切り替え
   - メニューバーから選択された言語ファイルをロード
   - UIコンポーネントの再描画
   - 設定ファイルの language 値を更新

## 8. テーマ設計

### 8.1 テーマファイル構造
```qss
/* テーマファイル（例：dark.qss）の構造 */
/* メインウィンドウのスタイル */
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

/* オーバーレイウィンドウのスタイル */
OverlayWindow {
    background-color: transparent;
    border: 1px solid #404040;
}

/* その他のUIコンポーネントのスタイル */
QPushButton {
    background-color: #3b3b3b;
    color: #ffffff;
    border: 1px solid #505050;
}
```

### 8.2 テーマファイル管理
- ThemeManager クラス
  - themes/フォルダからのテーマファイルの動的検出
  - 利用可能なテーマのメニューバーへの表示
  - テーマ切り替え処理
  - デフォルトテーマのフォールバック
  - スタイルシートの検証

### 8.3 テーマファイルの検出と表示
1. アプリケーション起動時
   - themes/フォルダ内の*.qssファイルを検索
   - 各テーマファイルの基本情報を読み込み
   - メニューバーのテーマ一覧を構築

2. テーマ切り替え時
   - 選択されたテーマファイルをロード
   - 設定ファイルの theme 値を更新
   - UIコンポーネントへの適用

### 8.4 テーマ化プロセス
1. アプリケーション起動時
   - themes/フォルダから利用可能なテーマファイルを検出
   - 設定ファイルから最後に使用したテーマ設定を読み込み
   - 対応するテーマファイルをロード
   - メニューバーのテーマ一覧を構築
   - UIへの適用

2. 実行時のテーマ切り替え
   - メニューバーから選択されたテーマファイルをロード
   - UIコンポーネントのスタイル更新
   - 設定ファイルの theme 値を更新

## 9. メモ機能設計

### 9.1 メモウィンドウ仕様
- フレームレス・最前面表示
- クリック操作無効
- 背景色と文字色の個別設定（透明対応）
- ウィンドウサイズと文字サイズの連動制御
- プレーンテキストのみサポート（マークダウン非対応）

### 9.2 メモ設定
```json
{
  "memo_settings": {
    "background_color": string,  // RGBA形式 (例: "#FFFFFF80")
    "text_color": string,       // RGB形式 (例: "#000000")
    "text_content": string,     // メモテキスト
    "window_size": {
      "width": number,
      "height": number
    }
  }
}
```

### 9.3 メモモード UI構成
1. メインウィンドウ
   - メモ入力テキストエリア
   - 表示設定
     - 透明度スライダー
     - サイズ調整スライダー
   - 詳細設定（折りたたみパネル）
     - 背景色選択
     - 文字色選択

2. オーバーレイウィンドウ
   - テキスト表示領域
   - 設定に応じた背景色/文字色の適用
   - サイズに応じた文字サイズの自動調整

## 10. マルチモニター設計

### 10.1 モニター管理
- モニター情報の取得と監視
- プライマリーモニターの識別
- モニター変更時の位置補正

### 10.2 モニター間の移動制限
- 各モニター内での移動のみ許可
- モニター変更時の座標系変換
- モニター選択UIでの切り替え

### 10.3 モニター設定の永続化
```json
{
  "monitor_settings": {
    "last_monitor": string,     // 前回選択したモニター名
    "fallback_primary": boolean // プライマリーモニターへのフォールバック
  }
}
```

## 11. ホットキー設計

### 11.1 ホットキー設定
```json
{
  "hotkey_settings": {
    "toggle_overlay": {
      "key": string,           // キー（例: "O"）
      "modifiers": string[],   // 修飾キー（例: ["Alt", "Shift"]）
    }
  }
}
```

### 11.2 デフォルト設定
- 表示/非表示切り替え: Alt + Shift + O

## 12. イメージ処理設計

### 12.1 サポート画像形式
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif) - アニメーション非対応
- BMP (.bmp)
- WEBP (.webp)

### 12.2 リサイズアルゴリズム
- Bilinear補間法: 通常の拡大縮小
- Bicubic補間法: 高品質モード
- Nearest Neighbor: 高速モード

### 12.3 画像処理の最適化
- キャッシュによる再描画の最小化
- 非同期読み込みによるUI応答性の確保
- メモリ使用量の監視と制御

## 13. プレビューウィジェット設計

### 13.1 表示仕様
- モニターのアスペクト比に合わせた表示
- オーバーレイの相対位置とサイズの視覚化
- 縦横比固定のリサイズ操作

### 13.2 操作機能
- ドラッグによる位置調整
- コーナーハンドルによるリサイズ
- リアルタイムプレビュー更新

### 13.3 座標変換
- プレビューウィジェット座標 ⟷ 実画面座標の相互変換
- スケーリング係数の動的計算
- 境界チェックと位置補正
