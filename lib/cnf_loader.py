import os
import json
from typing import Any, Dict, Optional

def cf_change(key: str, value: any) -> int:
    """
    configs/config.jsonのデータを編集する関数

    Args
    ----------
        key (str): 変更したい設定のキー
        value (any): 新しい値

    Returns
    ----------
    int: 変更された値の数
    """

    # 変更カウンター
    change_count = 0

    try:
        # JSONファイルを読み込む
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # キーが存在する場合は値を更新
        if key in config_data:
            if config_data[key] != value:
                config_data[key] = value
                change_count += 1

        # 変更をファイルに保存
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)

        return change_count

    except FileNotFoundError:
        raise FileNotFoundError("設定ファイルが見つかりません: " + config_path)
    except json.JSONDecodeError:
        raise ValueError("設定ファイルの形式が不正です")

def cf_load() -> object:
    """
    configs/config.jsonから設定データを取得する関数

    Returns
    ----------
        object: 変更された値の数
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"post_info": "md", "save_info": True}

def get_config_value(key: str, default: Any = None) -> Any:
    """
    設定値を取得する
    Args:
    ----------
        key (str): 設定キー
        default (Any): デフォルト値
    Returns:
    ----------
        Any: 設定値
    """
    return cf_load().get(key, default)

def save_window_state(window_pos: tuple, window_size: tuple) -> None:
    """
    ウィンドウの状態を保存
    Args:
    ----------
        window_pos (tuple): (x, y)
        window_size (tuple): (width, height)
    """
    cf_change("window_x", window_pos[0])
    cf_change("window_y", window_pos[1])
    cf_change("window_width", window_size[0])
    cf_change("window_height", window_size[1])

def save_overlay_state(size: int, alpha: int, pos: tuple, monitor: Optional[str]) -> None:
    """
    オーバーレイの状態を保存
    Args:
    ----------
        size (int): サイズ(%)
        alpha (int): 透明度(%)
        pos (tuple): (x, y)
        monitor (str): モニター名
    """
    cf_change("overlay_size", size)
    cf_change("overlay_alpha", alpha)
    cf_change("overlay_x", pos[0])
    cf_change("overlay_y", pos[1])
    cf_change("target_monitor_name", monitor if monitor is not None else "")

# 設定ファイルのパスを取得
config_path = "/configs/config.json"
config_path = os.path.join(os.getcwd() + config_path)
