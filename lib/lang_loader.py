import os
import json
import glob
from lib.cnf_loader import cf_load

def get_available_languages() -> list[str]:
    """利用可能な言語ファイルを検索して言語名のリストを返す"""
    languages = []
    langfile_dir = os.path.join(os.getcwd(), "languages")
    if os.path.exists(langfile_dir):
        for lang_file in glob.glob(os.path.join(langfile_dir, "*.json")):
            lang_name = os.path.splitext(os.path.basename(lang_file))[0]
            languages.append(lang_name)
    return sorted(languages) or ["Japanese", "English"]  # デフォルト言語を提供

def lang_load(lang_code : str = None) -> object:
    """
    言語コードに基づいて言語ファイルを読み込む
    Args
    ----------
        lang_code (str): 読み込みたい言語のコード
    """
    global config_data, langfile_dir, lang_data
    if lang_code is None:
        lang_code = config_data.get("language")
    lang_file = os.path.join(langfile_dir, f"{lang_code}.json")
    default_lang_file = os.path.join(langfile_dir, f"{'en'}.json")

    try:
        with open(lang_file, "r", encoding="utf-8") as file:
            lang_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"警告: 言語ファイル '{lang_code}.json' が見つからないか、無効です。デフォルト言語を使用します。")
        try:
            with open(default_lang_file, "r", encoding="utf-8") as file:
                lang_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print("エラー: デフォルト言語ファイル 'en.json' が見つからないか、無効です。プログラムを終了します。")
            exit(1)

def get_text(key, **key_args):
    """
    言語ファイルから言語コードに対応するメッセージを取得し、必要に応じてフォーマット
    Args
    ----------
        key (str): 抽出したい言語データのキー
        key_args (str): キーに埋め込む用の引数

    Returns:
    ----------
        object: 取り出した言語ファイルのjsonオブジェクト
    """
    global lang_data
    try:
        text = lang_data.get(key, key)
        return text.format(**key_args)
    except KeyError:
        return f"メッセージ '{key}' が見つかりません。"


def change_language(new_lang: str) -> bool:
    """
    言語を変更し、設定を保存する
    Args:
    ----------
        new_lang (str): 新しい言語名
    Returns:
    ----------
        bool: 変更が成功したかどうか
    """
    global config_data, lang_data
    try:
        if new_lang != config_data.get("language"):
            from lib.cnf_loader import cf_change
            cf_change("language", new_lang)
            lang_data = lang_load(new_lang)
            return lang_data is not None
    except Exception:
        return False
    return True


config_data = cf_load()
langfile_dir = os.getcwd() + "/languages"
lang_data   = lang_load()
