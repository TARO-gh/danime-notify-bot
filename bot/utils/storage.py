import os
import json
from discord import Embed

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


async def add_to_watchlist(ctx, work_id: int):
    """
    watchlistにアニメを追加し、結果をDiscordに通知する
    """
    save_data = _load_json('save_info.json')
    # 重複チェック
    if any(item['work_id'] == str(work_id) for item in save_data):
        await ctx.send(embed=Embed(
            title="既に追加されています。", color=0xff4500
        ), delete_after=60)
        return
    # 初期情報取得（fetch_initial_dataは scraper.py で定義）
    from bot.utils.scraper import fetch_initial_data
    info = await fetch_initial_data(work_id)
    if not info:
        await ctx.send(embed=Embed(
            title="アニメタイトルの追加に失敗しました。", color=0xff4500
        ), delete_after=60)
        return
    save_data.append(info)
    _save_json('save_info.json', save_data)
    url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}"
    embed = Embed(
        title="通知するアニメタイトルを追加しました。",
        description=f"{info['work_title']} (ID: {info['work_id']})\n{url}",
        color=0xff4500
    )
    embed.set_image(url=info['work_thumbnail_url'])
    embed.set_footer(text=f"追加者: {ctx.author.display_name}")
    await ctx.send(embed=embed)


async def remove_from_watchlist(ctx, work_id: int):
    """
    watchlistからアニメを削除し、結果をDiscordに通知する
    """
    save_data = _load_json('save_info.json')
    new_list = [item for item in save_data if item['work_id'] != str(work_id)]
    if len(new_list) == len(save_data):
        await ctx.send(embed=Embed(
            title="作品IDが存在しないか、追加されていません。", color=0xff4500
        ), delete_after=60)
        return
    # 削除アイテムの情報取得
    deleted = next(item for item in save_data if item['work_id'] == str(work_id))
    _save_json('save_info.json', new_list)
    embed = Embed(
        title="通知するアニメタイトルを削除しました。",
        description=f"{deleted['work_title']} (ID: {deleted['work_id']})",
        color=0xff4500
    )
    await ctx.send(embed=embed, delete_after=60)

async def clear_watchlist():
    """
    watchlistを全てクリアし、結果をDiscordに通知する
    """
    _save_json('save_info.json', [])
    return

async def load_watchlist():
    """
    watchlistをロードして返す
    """
    save_data = _load_json('save_info.json')
    return save_data if save_data else []