"""
環境変数・設定値の一元管理。

.env の読み込みと os.getenv をここに集約し、
他モジュールは bot.config から設定値を import して使う。
"""
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Discord Bot トークン（必須）
TOKEN = os.getenv("TOKEN")

# 通知対象のギルド / チャンネル
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID", 0))
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", 0))

# Chrome / Chromium バイナリのパス（Dockerを使わない場合に必要）
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
