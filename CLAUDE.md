# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Discord bot that monitors dアニメストア (d Anime Store) work pages via Selenium/Chromium and posts notifications to a Discord channel when watched anime get new episodes. Python + py-cord (Pycord) + Asyncio. Documentation and all user-facing strings are in Japanese.

## Commands

```bash
# Run locally (module form — required for the package-relative imports to resolve)
python -m bot.main

# Run via Docker (recommended; bundles chromium + chromium-driver)
docker-compose up -d --build
```

There is no test suite, linter, or build step configured. `requirements.txt` holds the dependencies (`pip install -r requirements.txt`); running outside Docker requires a local Chrome/Chromium and `CHROME_BIN` pointing at its binary.

## Environment

Configured via `.env` (see `.env.example`):
- `TOKEN` (required) — Discord bot token; `bot.main` raises if unset.
- `TARGET_GUILD_ID`, `TARGET_CHANNEL_ID` — the single guild/channel the bot serves. All notifications and command replies go to `TARGET_CHANNEL_ID`.
- `CHROME_BIN` (optional) — Chromium binary path, defaults to `/usr/bin/chromium`. Set in the Dockerfile.

## Architecture

**Entry point** — [bot/main.py](bot/main.py) creates a `bridge.Bot` (prefix `^`, all intents). On `on_ready` it resolves the target guild/channel, starts the update loop, and sets presence. `load_cogs()` auto-discovers every module in `bot/commands/` via `pkgutil.iter_modules` and calls its `setup(bot)` — **a new command is registered simply by dropping a file with a `setup()` in `bot/commands/`.**

**Commands** ([bot/commands/](bot/commands/)) — one Cog per file, each exposing a `bridge.bridge_command` (works as both a slash command and a `^`-prefixed message command). Commands: `add`, `del` (delete.py), `list`, `clear`, `search`, `schedule`, `update`, `lineup`. Convention: every command first calls `ctx.respond("...", delete_after=1)` to ack, then sends real output to `ctx.channel` with `delete_after=60` so the channel self-cleans. Embeds use color `0xff4500` throughout.

**Persistence** — [bot/utils/storage.py](bot/utils/storage.py). State is a single JSON file, `opt/save_info.json` (gitignored), an array of work records: `work_id`, `work_title`, `latest_part_id`, `latest_part_title`, thumbnails, `latest_update_date`, `schedule_day` (0=Mon … 6=Sun, 7=unknown), `schedule_time`. `_load_json`/`_save_json` resolve paths relative to the repo-root `opt/` dir. There is no DB and no locking — every read is a fresh full-file load.

**Update loop** — [bot/utils/checker.py](bot/utils/checker.py). A 1-second `tasks.loop` fires `check()` at minute :01 and :31 (a >5-min guard prevents double-firing). `check()` is guarded by a module-level `updating` flag against re-entrancy. Because a check can run for minutes (Selenium per work) while users add/remove entries concurrently, `check()` **re-reads the file at the end and merges the diff** (`orig_ids` vs `latest_ids`) before saving — preserve this merge logic when editing. A work with no successful fetch for >15 days is auto-deleted with a notification. `manual_check_updates()` (the `/update` command) calls the same `check()`.

**Manual notifications** — [bot/utils/manual.py](bot/utils/manual.py) + [bot/utils/manual_embeds.py](bot/utils/manual_embeds.py). A fully self-contained feature for non-dアニメストア titles: no Selenium, no stale auto-delete, no interaction with the watchlist. Its own JSON file (`opt/manual_info.json`, gitignored) holds records of `entry_id` (`m1`, `m2`, …), `title`, `schedule_day`, `schedule_time`, `image_url`, `last_notified`. A 30-second `tasks.loop` sends a notification when the current time is at/past the entry's weekday+time and `last_notified` is not today — the "at or past" condition means a notification missed while the bot was down is still sent on restart; `add_manual_entry` pre-sets `last_notified` when the time has already passed today so a new entry doesn't fire immediately. Times use a fixed JST offset (`dt.timezone`, no tzdata dependency), unlike the rest of the codebase which uses naive `datetime.now()`. Commands: `madd`, `mdel`, `mlist`. The only wiring into existing code is `start_manual_notify_loop(bot)` in `main.py`.

**Scraping** — [bot/utils/scraper.py](bot/utils/scraper.py). Each function spins up its own headless Chromium via Selenium, waits for JS-rendered elements, then parses with BeautifulSoup. Selectors are tightly coupled to dアニメストア's DOM (e.g. `span.note.schedule`, `a[id^=episodePartId]`, `img#modalThumbImg`, `div.itemModule.list[data-workid]`) — the most fragile part of the codebase; site markup changes break it. Timeouts return `None`/`[]` rather than raising (callers treat `None` as "skip this work"), except `fetch_initial_data` raises `ValueError` when a page has zero episodes. `fetch_lineup` tries several URL slug permutations for a season/year.

**Views** ([bot/views/](bot/views/)) — `discord.ui.View` subclasses for interactive replies: `SearchView` (select-menu to pick a search result to add), `ClearView` (confirm/cancel buttons for full wipe), `LineupView` (season-switcher select, windowed to 21 options). These modules are imported once in `main.py` (they self-register via their command Cogs, not via `load_cogs`).

**Season helpers** — [bot/utils/lineup.py](bot/utils/lineup.py) maps months→season (winter/spring/summer/fall) and formats Japanese labels. Embed builders live in [bot/utils/embeds.py](bot/utils/embeds.py).

## Notes

- Only public, non-`robots.txt`-restricted pages are scraped; no login or internal APIs (see README disclaimer).
- The `.mcp.json` (gitignored) configures a Playwright MCP server (headless chromium) — useful for manually inspecting the live dアニメストア DOM when selectors break.
