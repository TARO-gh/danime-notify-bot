import asyncio
import datetime as dt
from discord import Embed
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import urllib3
from urllib.parse import urljoin
from bot.utils.lineup import format_season_label
from bot.utils.robots import robots_checker, RobotsDisallowed
from bot.config import CHROME_BIN
from typing import Optional, List, Tuple
from contextlib import contextmanager


@contextmanager
def _chrome_driver():
    """設定済みのヘッドレスChromeドライバを生成し、終了時に必ずquitする。"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # バイナリの場所を明示（CHROME_BIN 未設定時は標準パス）
    options.binary_location = CHROME_BIN
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()


async def fetch_initial_data(work_id: int) -> dict:
    """
    指定されたwork_idから初回追加時の情報を取得して返す
    """
    print("--------------------------")
    print(f"[開始] 作品ID {work_id} の更新確認を開始します")
    url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}"
    # robots.txt で禁止されている場合は取得せず例外（呼び出し側で安全にスキップ）
    if not robots_checker.can_fetch(url):
        print(f"[robots] Disallow のため取得中止: {url}")
        raise RobotsDisallowed(url)
    try:
        with _chrome_driver() as driver:
            # ── 初回ロード ──
            print(f"[ロード] 初回ページ取得→ {url}")
            driver.set_page_load_timeout(40)
            try:
                driver.get(url)
            except (TimeoutException, urllib3.exceptions.ReadTimeoutError) as e:
                print(f"[タイムアウト] 初回ロード失敗: workId={work_id} → スキップ ({type(e).__name__})")
                return None

            # ── 動的要素待ち ──
            print(f"[待機] スケジュール要素レンダリング待ち")
            try:
                wait = WebDriverWait(driver, timeout=10, poll_frequency=1.0)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.note.schedule")))
                await asyncio.sleep(random.uniform(1.5, 3.0))
                print(f"[取得] スケジュール要素あり")
            except TimeoutException:
                print(f"[情報] スケジュール要素なし（最終回などの想定パターン）。デフォルトで続行")  # ★ ここで握りつぶして続行

            # htmlを取得
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            schedule_day, schedule_time = 7, "00:00"  # デフォルト値
            schedule_elem = soup.select_one(
                "body > div.pageWrapper > div > div.productWrapper.onlySpLayout > div > div > div > p > span.note.schedule"
            )
            if schedule_elem:
                text = schedule_elem.text.strip()
                day_char = text[text.find("曜") - 1]
                day_map = {"月":0, "火":1, "水":2, "木":3, "金":4, "土":5, "日":6}
                schedule_day = day_map.get(day_char, 7)
                nums = re.findall(r'\d+', text)
                schedule_time = f"{nums[0]}:{nums[1]}" if len(nums) >= 2 else "00:00"

            work_title = soup.title.get_text().split(" | ")[0].strip()
            print(f"[解析] タイトル: {work_title}, 放送曜日={schedule_day}, 時刻={schedule_time}")

            divs = soup.find_all("a", id=lambda x: x and x.startswith("episodePartId"))
            episodes = []
            for a in divs:
                pid = re.search(r"=(\d{8})", a["href"]).group(1)
                span = a.find_next("span", class_="ui-clamp webkit2LineClamp")
                if span:
                    episodes.append((pid, span.text.strip()))
            if not episodes:
                raise ValueError(f"作品ID {work_id} の情報が取得できませんでした。")
            latest_part_id, latest_part_title = episodes[-1]

            img_tag = soup.find("img", class_="lazyloaded")
            src_url = img_tag["src"] if img_tag else None

            # ── 最新話サムネ取得 ──
            part_url = f"{url}&partId={latest_part_id}"
            print(f"[ロード] 最新話ページ取得→ {part_url}")
            part_img_url = None
            try:
                driver.set_page_load_timeout(30)
                driver.get(part_url)
                WebDriverWait(driver, timeout=10).until(EC.presence_of_element_located((By.CLASS_NAME, "title")))
                await asyncio.sleep(5)
                part_soup = BeautifulSoup(driver.page_source, 'html.parser')
                part_img_url = part_soup.find('img', id='modalThumbImg')['data-src']
                if "1_3.png" in part_img_url:
                    part_img_url = part_img_url.replace("1_3.png", "1_1.png")
                print(f"[取得] 最新話サムネURL: {part_img_url}")  # 追加
            except (TimeoutException, urllib3.exceptions.ReadTimeoutError) as e:
                print(f"[タイムアウト] サムネ取得失敗: workId={work_id}, part={latest_part_id} → None ({type(e).__name__})")  # 変更

            return {
                "work_id": str(work_id),
                "work_title": work_title,
                "work_thumbnail_url": src_url,
                "latest_part_id": latest_part_id,
                "latest_part_title": latest_part_title,
                "latest_part_thumbnail_url": part_img_url,
                "latest_update_date": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "schedule_day": schedule_day,
                "schedule_time": schedule_time,
            }

    except Exception as e:
        print(f"[例外] workId={work_id} スキップ: {type(e).__name__} - {e}")
        return None

    finally:
        print(f"[終了] 作品ID {work_id} の更新確認を終了します")
        print("--------------------------")



def _extract_lineup_items(soup: BeautifulSoup) -> List[Tuple[str, str, bool]]:
    """
    ラインナップから (work_id, title, available) を抽出する。
    available=False は disableLink（配信リンク未活性＝配信開始前）の作品。
    """
    items: List[Tuple[str, str, bool]] = []
    seen: set[str] = set()

    # 第1戦略: ci_pc リンクから抽出（リンクがある＝配信中）
    for a in soup.select('a[href*="ci_pc?workId="]'):
        href = a.get('href')
        if not href:
            continue
        match = re.search(r'workId=(\d+)', href)
        if not match:
            continue
        work_id = match.group(1)
        if work_id in seen:
            continue
        title_elem = a.select_one('h3') or a.select_one('p')
        title = title_elem.get_text(strip=True) if title_elem else a.get_text(strip=True)
        if not title:
            continue
        items.append((work_id, title, True))
        seen.add(work_id)

    # 第2戦略: itemModule タイルで取りこぼしを補完（常に実行）。
    #   disableLink（配信開始前）の作品は ci_pc リンクを持たず第1戦略で漏れるため、
    #   data-workid から拾い、available=False として区別する。
    #   ※ find_all(class_='itemModule list') はスペース入り文字列だと完全一致となり
    #     class="itemModule list disableLink" にマッチしないため、CSSセレクタで部分集合マッチする。
    for div in soup.select('div.itemModule.list'):
        work_id = div.get('data-workid')
        if not work_id or work_id in seen:
            continue
        title_elem = (
            div.select_one('h3')
            or div.select_one('p')
            or div.select_one('span.ui-clamp.webkit2LineClamp')
        )
        title = title_elem.get_text(strip=True) if title_elem else None
        if not title:
            continue
        available = 'disableLink' not in div.get('class', [])
        items.append((work_id, title, available))
        seen.add(work_id)

    if items:
        return items

    # フォールバック: itemModule 構造が無いページ向け
    for node in soup.select('[data-workid]'):
        work_id = node.get('data-workid')
        if not work_id or work_id in seen:
            continue
        title_elem = node.select_one('span.ui-clamp.webkit2LineClamp') or node.select_one('span.ui-clamp')
        title = title_elem.get_text(strip=True) if title_elem else None
        if title:
            items.append((work_id, title, True))
            seen.add(work_id)

    if items:
        return items

    for a in soup.select('a[href*="workId="]'):
        href = a.get('href')
        if not href:
            continue
        match = re.search(r'workId=(\d+)', href)
        if not match:
            continue
        work_id = match.group(1)
        if work_id in seen:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        items.append((work_id, title, True))
        seen.add(work_id)

    return items


def _build_lineup_urls(season: str, year: Optional[int], use_base_only: bool) -> List[str]:
    base = "https://animestore.docomo.ne.jp/animestore/CF/"
    if use_base_only or year is None:
        return [f"{base}{season}"]
    return [
        f"{base}{season}_{year}",
        f"{base}{year}_{season}",
        f"{base}{season}{year}",
        f"{base}{season}-{year}",
        f"{base}{year}{season}",
    ]


async def _fetch_lineup_url(url: str) -> List[Tuple[str, str, bool]]:
    if not robots_checker.can_fetch(url):
        print(f"[robots] Disallow のため取得中止: {url}")
        return []
    try:
        with _chrome_driver() as driver:
            print(f"[ロード] ラインナップページ取得→ {url}")
            driver.set_page_load_timeout(40)
            driver.get(url)
            try:
                wait = WebDriverWait(driver, timeout=10, poll_frequency=1.0)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="ci_pc?workId="]')))
                await asyncio.sleep(random.uniform(1.5, 3.0))
                print("[取得] ラインナップ要素あり")
            except TimeoutException:
                print("[情報] ラインナップ要素待機タイムアウト")
                pass
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            items = _extract_lineup_items(soup)
            print(f"[解析] ラインナップ件数: {len(items)}")
            return items
    except (TimeoutException, urllib3.exceptions.ReadTimeoutError):
        return []


async def fetch_lineup(season: str, year: Optional[int] = None, use_base_only: bool = False) -> List[Tuple[str, str]]:
    urls = _build_lineup_urls(season, year, use_base_only)
    for url in urls:
        items = await _fetch_lineup_url(url)
        if items:
            return items
    return []


def _extract_lineup_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    seen: set[str] = set()
    season_pattern = re.compile(r'/(?:animestore/)?CF/([^/?#]+)')
    token_pattern = re.compile(r'(winter|spring|summer|fall).*?(20\d{2})|(20\d{2}).*?(winter|spring|summer|fall)')
    allow_token = re.compile(
        r'^(winter|spring|summer|fall|shinban-|tv-rendou-haishin-list-past-)'
    )

    for a in soup.select('a[href]'):
        href = a.get('href')
        if not href:
            continue
        if not allow_token.search(href):
            continue
        full_url = urljoin(base_url, f"/animestore/CF/{href}")
        if full_url in seen:
            continue
        seen.add(full_url)

        label = a.get_text(strip=True)
        if not label:
            token_match = token_pattern.search(href)
            if token_match:
                season = token_match.group(1) or token_match.group(4)
                year = token_match.group(2) or token_match.group(3)
                if season and year:
                    label = format_season_label(int(year), season)
        if not label:
            label = "ラインナップ"
        links.append((label, full_url))

    return links


async def fetch_lineup_from_url(url: str) -> List[Tuple[str, str]]:
    return await _fetch_lineup_url(url)


async def fetch_lineup_current_with_links(season: str) -> Tuple[List[Tuple[str, str, bool]], List[Tuple[str, str]]]:
    url = f"https://animestore.docomo.ne.jp/animestore/CF/{season}"
    if not robots_checker.can_fetch(url):
        print(f"[robots] Disallow のため取得中止: {url}")
        return [], []
    try:
        with _chrome_driver() as driver:
            print(f"[ロード] 今季ラインナップページ取得→ {url}")
            driver.set_page_load_timeout(40)
            driver.get(url)
            try:
                wait = WebDriverWait(driver, timeout=10, poll_frequency=1.0)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="ci_pc?workId="]')))
                await asyncio.sleep(random.uniform(1.5, 3.0))
                print("[取得] ラインナップ要素あり")
            except TimeoutException:
                print("[情報] ラインナップ要素待機タイムアウト")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            items = _extract_lineup_items(soup)
            links = _extract_lineup_links(soup, url)
            print(f"[解析] ラインナップ件数: {len(items)}, リンク件数: {len(links)}")
            return items, links
    except (TimeoutException, urllib3.exceptions.ReadTimeoutError):
        return [], []
