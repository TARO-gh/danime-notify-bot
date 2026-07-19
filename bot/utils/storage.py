import os
import json

# opt ディレクトリへのパス設定
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'opt'))


def _load_json(filename: str):
    """
    JSONファイルを読み込んでデータを返す
    """
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(filename: str, data):
    """
    データをJSONファイルに書き込む
    """
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def add_to_watchlist(work_id: int):
    """
    watchlist にアニメを追加する。表示は行わず、結果ステータスを返す。
    戻り値: (status, info)
      - ("duplicate", None) : 既に登録済み
      - ("robots", None)    : robots.txt により取得不可
      - ("failed", None)    : 取得失敗（配信開始前 or ID不正）
      - ("ok", info)        : 追加成功
    """
    save_data = _load_json('save_info.json')
    # 重複チェック
    if any(item['work_id'] == str(work_id) for item in save_data):
        return ("duplicate", None)
    # 初期情報取得（fetch_initial_dataは scraper.py で定義）
    from bot.utils.scraper import fetch_initial_data
    from bot.utils.robots import RobotsDisallowed
    try:
        info = await fetch_initial_data(work_id)
    except RobotsDisallowed:
        return ("robots", None)
    if not info:
        return ("failed", None)
    save_data.append(info)
    _save_json('save_info.json', save_data)
    return ("ok", info)


async def remove_from_watchlist(work_id: int):
    """
    watchlist からアニメを削除する。表示は行わず、結果ステータスを返す。
    戻り値: (status, deleted)
      - ("not_found", None) : 未登録
      - ("ok", deleted)     : 削除成功
    """
    save_data = _load_json('save_info.json')
    new_list = [item for item in save_data if item['work_id'] != str(work_id)]
    if len(new_list) == len(save_data):
        return ("not_found", None)
    deleted = next(item for item in save_data if item['work_id'] == str(work_id))
    _save_json('save_info.json', new_list)
    return ("ok", deleted)


async def clear_watchlist():
    """
    watchlistを全てクリアする
    """
    _save_json('save_info.json', [])
    return


async def load_watchlist():
    """
    watchlistをロードして返す
    """
    save_data = _load_json('save_info.json')
    return save_data if save_data else []
