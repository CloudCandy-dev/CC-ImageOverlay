# ApplicationSettings 詳細設計

## 1. 概要
アプリケーション全体の設定を管理するエンティティクラス。メインウィンドウの位置、サイズ、言語設定、テーマ設定などを保持する。

## 2. クラス定義

```python
class ApplicationSettings:
    """アプリケーション設定クラス"""
    
    def __init__(self):
        self._window_position = QPoint(100, 100)
        self._window_size = QSize(800, 600)
        self._language = "Japanese.json"
        self._theme = "dark.qss"
        self._last_image_path = ""

    @property
    def window_position(self) -> QPoint:
        """ウィンドウ位置を取得"""
        return self._window_position

    @window_position.setter
    def window_position(self, value: QPoint) -> None:
        """ウィンドウ位置を設定"""
        self._window_position = value

    @property
    def window_size(self) -> QSize:
        """ウィンドウサイズを取得"""
        return self._window_size

    @window_size.setter
    def window_size(self, value: QSize) -> None:
        """ウィンドウサイズを設定"""
        self._window_size = value

    @property
    def language(self) -> str:
        """言語設定を取得"""
        return self._language

    @language.setter
    def language(self, value: str) -> None:
        """言語設定を更新"""
        self._language = value

    @property
    def theme(self) -> str:
        """テーマ設定を取得"""
        return self._theme

    @theme.setter
    def theme(self, value: str) -> None:
        """テーマ設定を更新"""
        self._theme = value

    @property
    def last_image_path(self) -> str:
        """最後に使用した画像パスを取得"""
        return self._last_image_path

    @last_image_path.setter
    def last_image_path(self, value: str) -> None:
        """最後に使用した画像パスを更新"""
        self._last_image_path = value

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplicationSettings':
        """辞書から設定を生成"""
        instance = cls()
        if not data:
            return instance

        window = data.get("window", {})
        instance.window_position = QPoint(
            window.get("x", 100),
            window.get("y", 100)
        )
        instance.window_size = QSize(
            window.get("width", 800),
            window.get("height", 600)
        )
        instance.language = data.get("language", "Japanese.json")
        instance.theme = data.get("theme", "dark.qss")
        instance.last_image_path = data.get("last_image_path", "")
        return instance

    def to_dict(self) -> dict:
        """設定を辞書形式に変換"""
        return {
            "window": {
                "x": self.window_position.x(),
                "y": self.window_position.y(),
                "width": self.window_size.width(),
                "height": self.window_size.height()
            },
            "language": self.language,
            "theme": self.theme,
            "last_image_path": self.last_image_path
        }
```

## 3. 依存関係

### 3.1 必要なインポート
```python
from PySide6.QtCore import QPoint, QSize
```

## 4. 設定項目の詳細

### 4.1 ウィンドウ設定
- 位置 (x, y)
  - デフォルト: (100, 100)
  - 画面内に収まるように自動調整

- サイズ (width, height)
  - デフォルト: (800, 600)
  - 最小: (400, 300)
  - 最大: 画面サイズに依存

### 4.2 言語設定
- ファイル名形式: "{言語名}.json"
- デフォルト: "Japanese.json"
- languages/フォルダ内のファイルから動的に選択可能

### 4.3 テーマ設定
- ファイル名形式: "{テーマ名}.qss"
- デフォルト: "dark.qss"
- themes/フォルダ内のファイルから動的に選択可能

### 4.4 最後に使用した画像パス
- 相対パスまたは絶対パス
- 空文字列の場合は未設定

## 5. バリデーション

### 5.1 ウィンドウ位置の検証
- 画面範囲内に収まるように調整
- マルチモニター環境を考慮

### 5.2 ウィンドウサイズの検証
- 最小・最大サイズの範囲内に制限
- アスペクト比の考慮は不要

### 5.3 ファイル名の検証
- 言語ファイル: 存在確認、JSON形式
- テーマファイル: 存在確認、QSS形式

## 6. シリアライズ

### 6.1 JSON変換
- from_dict: JSON辞書から設定オブジェクトを生成
- to_dict: 設定オブジェクトをJSON辞書に変換
- 不正な値は適切なデフォルト値で補完

## 7. エラー処理

### 7.1 想定されるエラー
- 無効なウィンドウ位置・サイズ
- 存在しない言語/テーマファイル
- 無効なファイルパス

### 7.2 エラー処理方針
- 無効な値はデフォルト値で補完
- エラーログを出力
- 例外は上位層で捕捉
