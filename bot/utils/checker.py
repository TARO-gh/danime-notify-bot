import asyncio
import discord
from discord.ext import tasks
from discord import Embed
from bot.utils.storage import _load_json, _save_json
from bot.utils.storage import add_to_watchlist  # 必要に応じて
from bot.utils.scraper import fetch_initial_data  # 必要に応じて
import datetime as dt
import os
from dotenv import load_dotenv
import selenium


load_dotenv()  # 環境変数読み込み
CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))
updating = False

last_check_dt = dt.datetime(2000,1,1,0,0,0)
def start_update_loop(bot):
    @tasks.loop(seconds=1)
    async def update_loop():
        # 定期実行
        await bot.wait_until_ready()
        global last_check_dt
        dt_now = dt.datetime.now()
        if ((dt_now.minute == 1) or (dt_now.minute == 31)) and (dt_now - last_check_dt > dt.timedelta(minutes=5)):
            last_check_dt = dt_now
            await check(bot)

    update_loop.start()

async def manual_check_updates(bot) -> Embed:
    # 手動更新確認
    await check(bot)
    return Embed(title="更新確認処理が終了しました。", description="", color=0xff4500)

async def check(bot):
    """
    保存データを読み込み、データ取得/更新を行い、通知および保存更新
    """
    global updating
    if updating:
        print("更新確認は既に実行中です。")
        return
    try: 
        updating = True
        print(f"更新確認開始: {dt.datetime.now()}")
        data = _load_json('save_info.json')
        channel = bot.get_channel(CHANNEL_ID)
        del_workid_list = []

        for idx, item in enumerate(data):
            await bot.change_presence(activity=discord.Activity(name=f"更新確認中...({idx+1}/{len(data)})", type=discord.ActivityType.playing))
            work_id = item['work_id']
            latest_update_date_dt = dt.datetime.strptime(
                item['latest_update_date'], "%Y-%m-%d %H:%M:%S"
            )
            try:
                # 最新データ取得
                info = await fetch_initial_data(int(work_id))
            except selenium.common.exceptions.TimeoutException as e:
                continue
            
            # 取得できなかった場合はスキップ
            if not info:
                print(f"作品ID {work_id} の情報が取得できませんでした。スキップします。")
                continue

            # 変化があれば通知
            if info['latest_part_id'] != item.get('latest_part_id'):
                item.update(info)
                url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}&partId={info['latest_part_id']}"
                embed = Embed(
                    title="以下のアニメが更新されました。",
                    description=f"{info['work_title']}\n第{int(info['latest_part_id'][-3:])}話: {info['latest_part_title']}\n{url}",
                    color=0xff4500
                )
                embed.set_image(url=info['latest_part_thumbnail_url'])
                await channel.send(embed=embed)
            else:
                # 2週間と1日以上更新がない場合は削除
                if dt.datetime.now() - latest_update_date_dt > dt.timedelta(days=15):
                    del_workid_list.append(work_id)
                # スケジュール更新のみ
                item['schedule_day'] = info['schedule_day']
                item['schedule_time'] = info['schedule_time']
        
        # 差分マージ（確認処理中に追加削除されたものに対応）
        orig_ids = {item['work_id'] for item in data}
        latest_file = _load_json('save_info.json')
        latest_ids  = {it['work_id'] for it in latest_file}

        # 途中で追加された作品を確認
        added_ids = latest_ids - orig_ids
        if added_ids:
            print("途中追加を確認:", added_ids)
            for it in latest_file:
                if it['work_id'] in added_ids:
                    data.append(it)

        # 途中で削除された作品を確認
        removed_ids = orig_ids - latest_ids
        if removed_ids:
            print("途中削除を確認:", removed_ids)
            data = [it for it in data if it['work_id'] not in removed_ids] 
        
        # 自動削除リストに載った作品を削除
        if del_workid_list:
            print("自動削除対象:", del_workid_list)
            # save_info.json から削除
            data = [item for item in data if item['work_id'] not in del_workid_list]

        _save_json('save_info.json', data)
    finally: 
        updating = False
        await bot.change_presence(
            activity=discord.Activity(
                name="dアニメストアを30分に1回確認します。", 
                type=discord.ActivityType.playing
            )
        )
        print(f"更新確認終了: {dt.datetime.now()}")
