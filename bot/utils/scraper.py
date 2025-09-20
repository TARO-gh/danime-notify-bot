import asyncio
import datetime as dt
from discord import Embed
import re
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import urllib3


async def fetch_initial_data(work_id: int) -> dict:
    """
    指定されたwork_idから初回追加時の情報を取得して返す
    """
    print("--------------------------")
    print(f"[開始] 作品ID {work_id} の更新確認を開始します")
    url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # バイナリの場所を明示
    chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
    options.binary_location = chrome_bin
    driver = webdriver.Chrome(options=options)
    try:
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
        driver.quit()
        print(f"[終了] 作品ID {work_id} の更新確認を終了します")
        print("--------------------------")
    


async def search_anime(query: str) -> (list):
    """
    アニメを検索し、Embedと[(work_id, title), ...]を返す
    """
    url = f"https://animestore.docomo.ne.jp/animestore/sch_pc?searchKey={query}&vodTypeList=svod_tvod&sortKey=4"
    # Selenium用のドライバをセットアップ
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')  # ヘッドレスモード（ブラウザを表示しない）
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # バイナリの場所を明示
    chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    await asyncio.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    driver.quit()

    # data-workidを持つdivタグを探す
    divs = soup.find_all('div', class_='itemModule list')
    titles = soup.find_all('span', class_='ui-clamp webkit2LineClamp')

    # data-workid属性の値を取得
    data_workids = [div['data-workid'] for div in divs if 'data-workid' in div.attrs]

    results = list(zip(data_workids,titles))

    return results