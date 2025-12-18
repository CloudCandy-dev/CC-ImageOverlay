# ThemeStorage 詳細設計

## 1. 概要
アプリケーションのテーマファイル（QSSスタイルシート）の管理と永続化を担当するクラス。テーマファイルの読み込み、検証、キャッシュ管理を行う。

## 2. クラス定義

```python
class ThemeStorage:
    """テーマファイルの永続化を管理するクラス"""
    
    def __init__(self, theme_dir: str = "themes"):
        self._theme_dir = theme_dir
        self._theme_cache = {}
        self._default_theme = "light"
        self._current_theme = None
        self._lock = threading.Lock()

    def initialize(self) -> bool:
        """テーマストレージの初期化"""
        try:
            os.makedirs(self._theme_dir, exist_ok=True)
            self._validate_default_themes()
            return True
        except Exception as e:
            logger.error(f"テーマストレージの初期化に失敗: {e}")
            return False

    def get_available_themes(self) -> list[str]:
        """利用可能なテーマの一覧を取得"""
        themes = []
        try:
            for file in os.listdir(self._theme_dir):
                if file.endswith('.qss'):
                    themes.append(os.path.splitext(file)[0])
        except Exception as e:
            logger.error(f"テーマ一覧の取得に失敗: {e}")
        return themes

    def load_theme(self, theme_name: str) -> str:
        """テーマファイルを読み込む"""
        with self._lock:
            try:
                if theme_name in self._theme_cache:
                    return self._theme_cache[theme_name]

                theme_path = self._get_theme_path(theme_name)
                if not os.path.exists(theme_path):
                    logger.warning(f"テーマファイルが見つかりません: {theme_name}")
                    return self._load_default_theme()

                with open(theme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if self._validate_theme_content(content):
                        self._theme_cache[theme_name] = content
                        self._current_theme = theme_name
                        return content
                    return self._load_default_theme()
            except Exception as e:
                logger.error(f"テーマの読み込みに失敗: {e}")
                return self._load_default_theme()

    def save_theme(self, theme_name: str, content: str) -> bool:
        """テーマファイルを保存"""
        with self._lock:
            try:
                if not self._validate_theme_content(content):
                    return False

                theme_path = self._get_theme_path(theme_name)
                with open(theme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self._theme_cache[theme_name] = content
                return True
            except Exception as e:
                logger.error(f"テーマの保存に失敗: {e}")
                return False

    def get_current_theme(self) -> str:
        """現在のテーマ名を取得"""
        return self._current_theme or self._default_theme

    def _get_theme_path(self, theme_name: str) -> str:
        """テーマファイルのパスを取得"""
        return os.path.join(self._theme_dir, f"{theme_name}.qss")

    def _validate_theme_content(self, content: str) -> bool:
        """テーマ内容の検証"""
        try:
            # 基本的な構文チェック
            if not content.strip():
                return False

            # 必須のセレクタの存在チェック
            required_selectors = [
                "QMainWindow",
                "QWidget",
                "QPushButton",
                "QLabel"
            ]
            return all(selector in content for selector in required_selectors)
        except Exception:
            return False

    def _validate_default_themes(self) -> None:
        """デフォルトテーマファイルの検証と作成"""
        default_themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme()
        }

        for theme_name, content in default_themes.items():
            theme_path = self._get_theme_path(theme_name)
            if not os.path.exists(theme_path):
                self.save_theme(theme_name, content)

    def _load_default_theme(self) -> str:
        """デフォルトテーマの読み込み"""
        return self.load_theme(self._default_theme)

    def _get_light_theme(self) -> str:
        """ライトテーマのデフォルト定義"""
        return """
QMainWindow {
    background-color: #f0f0f0;
}

QWidget {
    color: #000000;
    background-color: #ffffff;
}

QPushButton {
    background-color: #e0e0e0;
    border: 1px solid #b0b0b0;
    padding: 5px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #d0d0d0;
}

QLabel {
    color: #000000;
}
"""

    def _get_dark_theme(self) -> str:
        """ダークテーマのデフォルト定義"""
        return """
QMainWindow {
    background-color: #2d2d2d;
}

QWidget {
    color: #ffffff;
    background-color: #3d3d3d;
}

QPushButton {
    background-color: #4d4d4d;
    border: 1px solid #5d5d5d;
    padding: 5px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #5d5d5d;
}

QLabel {
    color: #ffffff;
}
"""
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import threading
from typing import Dict, List, Optional
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 テーマ管理
1. テーマファイルの検索
2. デフォルトテーマの提供
3. テーマの検証
4. キャッシュの管理
5. ファイルシステムとの同期

### 4.2 テーマの読み込み
1. キャッシュチェック
2. ファイル存在確認
3. 内容の検証
4. スタイルシートの解析
5. キャッシュへの保存

### 4.3 テーマの保存
1. 内容の検証
2. ファイルの作成
3. パーミッションの設定
4. キャッシュの更新
5. エラー処理

## 5. エラー処理

### 5.1 想定されるエラー
- ファイルが存在しない
- 無効なQSSシンタックス
- 必須セレクタの欠落
- 書き込み権限なし
- ディスク容量不足

### 5.2 エラー処理方針
- ファイル不在 → デフォルトテーマを使用
- 構文エラー → テーマを無効化
- 権限エラー → エラーログを記録
- ディスク不足 → キャッシュを使用
- 検証失敗 → デフォルト値にフォールバック

## 6. スレッド安全性

### 6.1 排他制御
- キャッシュアクセスのロック
- ファイル操作の保護
- テーマ切り替えの同期

### 6.2 同時アクセス制御
- 読み取り優先度の設定
- 書き込み操作の直列化
- デッドロック防止

## 7. パフォーマンス考慮事項

### 7.1 キャッシュ管理
- メモリ使用量の制御
- キャッシュの有効期限
- 更新チェックの最適化

### 7.2 ファイルI/O
- バッファリングの活用
- 非同期読み込みの検討
- ディスクアクセスの最小化

## 8. デフォルトテーマ

### 8.1 ライトテーマ
- 白色ベース
- 高コントラスト
- システム標準に近い配色
- アクセシビリティ対応

### 8.2 ダークテーマ
- 暗色ベース
- 目の疲れを軽減
- モダンな見た目
- カスタマイズ可能な要素
