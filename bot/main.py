import os
from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import bridge
import pkgutil, importlib

# 更新チェックループ
from bot.utils.checker import start_update_loop

# Discord UIビュー
import bot.views.clear_view
import bot.views.search_view

import bot.commands as commands_pkg

# 環境変数読み込み
load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID", 0))
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))

# Botの初期化
bot = bridge.Bot(
    command_prefix='^',
    intents=discord.Intents.all(),
)

target_guild = None
channel = None

@bot.event
async def on_ready():
    global target_guild, channel
    # 起動ログ
    print(f"Bot is ready. Guild/Channel: {TARGET_GUILD_ID}/{TARGET_CHANNEL_ID}")

    # 対象ギルドとチャンネルを設定
    for guild in bot.guilds:
        if guild.id == TARGET_GUILD_ID:
            target_guild = guild
            break
    channel = bot.get_channel(TARGET_CHANNEL_ID)

    # 更新チェックループ開始
    start_update_loop(bot)

    # プレゼンス設定
    await bot.change_presence(
        activity=discord.Activity(
            name="dアニメストアを30分に1回確認します。", 
            type=discord.ActivityType.playing
        )
    )

def load_cogs():
    for finder, name, ispkg in pkgutil.iter_modules(commands_pkg.__path__):
        module = importlib.import_module(f"bot.commands.{name}")
        if hasattr(module, "setup"):
            module.setup(bot)

if __name__ == '__main__':
    if TOKEN is None:
        raise ValueError("TOKEN is not set. Please configure .env file.")
    load_cogs()
    bot.run(TOKEN)
