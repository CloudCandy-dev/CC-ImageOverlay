# LanguageManager 詳細設計

## 1. 概要
多言語対応のための言語リソース管理を担当するビューモデルクラス。言語リソースの読み込み、切り替え、テキスト取得のインターフェースを提供する。

## 2. クラス定義

```python
class LanguageManager(QObject):
    """言語管理ビューモデル"""

    languageChanged = Signal(str)  # 言語変更シグナル
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self._config_manager = config_manager
        self._current_language = "Japanese"
        self._language_data = {}
        self._available_languages = {}
        self._default_language = "Japanese"
        self._language_dir = "languages"

    @property
    def current_language(self) -> str:
        """現在の言語を取得"""
        return self._current_language

    @property
    def available_languages(self) -> Dict[str, str]:
        """利用可能な言語の一覧を取得"""
        return self._available_languages.copy()

    def initialize(self) -> bool:
        """言語マネージャの初期化"""
        try:
            self._load_available_languages()
            saved_lang = self._config_manager.get_value(
                "app_settings.language", self._default_language
            )
            return self.set_language(saved_lang)
        except Exception as e:
            logger.error(f"言語マネージャの初期化に失敗: {e}")
            return self.set_language(self._default_language)

    def set_language(self, language: str) -> bool:
        """言語の設定"""
        try:
            if language not in self._available_languages:
                logger.error(f"未対応の言語: {language}")
                return False

            if self._current_language == language:
                return True

            if self._load_language_data(language):
                self._current_language = language
                self._config_manager.set_value("app_settings.language", language)
                self.languageChanged.emit(language)
                return True
            return False

        except Exception as e:
            logger.error(f"言語設定に失敗: {e}")
            return False

    def get_text(self, key: str, default: str = "") -> str:
        """指定キーのテキストを取得"""
        try:
            # ネストしたキーに対応（例: "menu.file.open"）
            current = self._language_data
            for part in key.split('.'):
                if not isinstance(current, dict):
                    return default
                current = current.get(part, None)
                if current is None:
                    return default
            return str(current) if current is not None else default

        except Exception as e:
            logger.error(f"テキスト取得に失敗: {e}")
            return default

    def _load_available_languages(self) -> None:
        """利用可能な言語の読み込み"""
        try:
            self._available_languages.clear()
            for file in os.listdir(self._language_dir):
                if file.endswith('.json'):
                    lang_name = os.path.splitext(file)[0]
                    with open(os.path.join(self._language_dir, file), 'r', 
                             encoding='utf-8') as f:
                        data = json.load(f)
                        native_name = data.get('language.name', lang_name)
                        self._available_languages[lang_name] = native_name
        except Exception as e:
            logger.error(f"言語リストの読み込みに失敗: {e}")
            self._available_languages = {"Japanese": "日本語"}

    def _load_language_data(self, language: str) -> bool:
        """言語データの読み込み"""
        try:
            file_path = os.path.join(self._language_dir, f"{language}.json")
            if not os.path.exists(file_path):
                logger.error(f"言語ファイルが存在しません: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as f:
                self._language_data = json.load(f)
            return True

        except Exception as e:
            logger.error(f"言語データの読み込みに失敗: {e}")
            return False

    def format_text(self, key: str, *args, **kwargs) -> str:
        """テキストの書式設定"""
        try:
            template = self.get_text(key, key)
            return template.format(*args, **kwargs)
        except Exception as e:
            logger.error(f"テキスト書式設定に失敗: {e}")
            return key
```

## 3. 依存関係

### 3.1 必要なインポート
```python
import os
import json
from typing import Dict
from PySide6.QtCore import QObject, Signal
from ..services.config_manager import ConfigManager
from ..services.logging_service import logger
```

## 4. 主要機能の詳細

### 4.1 言語管理
1. 言語リストの読み込み
2. 言語データの取得
3. 言語切り替え
4. 設定の永続化
5. 変更通知

### 4.2 テキスト処理
1. キーによる検索
2. デフォルト値の提供
3. 書式設定
4. エラー処理
5. キャッシュ管理

### 4.3 リソース管理
1. ファイル読み込み
2. JSON解析
3. メモリ管理
4. エラー処理
5. 初期化処理

## 5. データ構造

### 5.1 言語ファイル形式
```json
{
    "language": {
        "name": "日本語",
        "code": "ja"
    },
    "menu": {
        "file": {
            "open": "開く",
            "save": "保存",
            "exit": "終了"
        }
    }
}
```

### 5.2 キー規則
- ドット区切りの階層構造
- ASCII文字のみ使用
- 小文字推奨
- 名前空間の使用

## 6. エラー処理

### 6.1 想定されるエラー
- ファイル不在
- JSON解析エラー
- 無効なキー
- メモリ不足
- I/Oエラー

### 6.2 エラー処理方針
- ファイル不在 → デフォルト言語
- 解析エラー → 空のデータ
- 無効キー → デフォルト値
- メモリ不足 → キャッシュクリア
- I/Oエラー → エラーログ記録

## 7. パフォーマンス最適化

### 7.1 キャッシュ戦略
- 言語データのキャッシュ
- 頻出キーの最適化
- メモリ使用量制御
- 遅延読み込み
- キャッシュ更新

### 7.2 リソース管理
- ファイルハンドルの制御
- メモリリークの防止
- 定期的なクリーンアップ
- リソースの解放
- 状態の監視

## 8. 拡張性

### 8.1 新規言語追加
- 言語ファイルの配置
- 自動検出
- 動的読み込み
- バリデーション
- エラー通知

### 8.2 カスタマイズ
- フォーマット指定
- プレースホルダー
- 条件付きテキスト
- 複数形対応
- 地域設定
