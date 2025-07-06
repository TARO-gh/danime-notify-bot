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
from bs4 import BeautifulSoup
import urllib3


async def fetch_initial_data(work_id: int) -> dict:
    """
    指定されたwork_idから初回追加時の情報を取得して返す
    """
    url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # バイナリの場所を明示
    chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
    options.binary_location = chrome_bin
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    wait = WebDriverWait(driver, timeout=10, poll_frequency=1.0)
    # 動的なHTML生成を待つ
    modal_body = wait.until(EC.presence_of_element_located(
    (By.CSS_SELECTOR, "span.note.schedule")
    ))
    random_sleep_time = random.uniform(1.5, 8.5) 
    await asyncio.sleep(random_sleep_time)  # ランダムな待機時間を追加
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    driver.quit()

    # スケジュール情報取得
    schedule_elem = soup.select_one(
        "body > div.pageWrapper > div > div.productWrapper.onlySpLayout > div > div > div > p > span.note.schedule"
    )
    if schedule_elem:
        text = schedule_elem.text.strip()
        day_char = text[text.find("曜") - 1]
        day_map = {"月":0, "火":1, "水":2, "木":3, "金":4, "土":5, "日":6}
        schedule_day = day_map.get(day_char, 7)
        time_nums = re.findall(r'\d+', text)
        schedule_time = f"{time_nums[0]}:{time_nums[1]}" if len(time_nums) >= 2 else "00:00"
    else:
        schedule_day = 7
        schedule_time = "00:00"

    # タイトル取得
    work_title = soup.title.get_text().split(" | ")[0].strip()

    # 各話情報取得
    divs = soup.find_all("a", id=lambda x: x and x.startswith("episodePartId"))
    episodes = []
    for a in divs:
        pid = re.search(r"=(\d{8})", a["href"]).group(1)
        # リンクの次にある span を探す（エピソードタイトル）
        title_span = a.find_next("span", class_="ui-clamp webkit2LineClamp")
        if not title_span:
            continue
        title = title_span.text.strip()
        episodes.append((pid, title))

    if not episodes:
        raise ValueError(f"作品ID {work_id} の情報が取得できませんでした。")

    latest_part_id, latest_part_title = episodes[-1]

    # <img>タグを検索してsrc属性を取得
    img_tag = soup.find("img", class_="lazyloaded")  # 特定のクラスを持つ<img>タグを検索
    if img_tag:
        src_url = img_tag["src"]  # src属性を取得

    # 最新話のサムネイルを取得
    url = f"https://animestore.docomo.ne.jp/animestore/ci_pc?workId={work_id}&partId={latest_part_id}"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # バイナリの場所を明示
    chrome_bin = os.getenv('CHROME_BIN', '/usr/bin/chromium')
    options.binary_location = chrome_bin
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, timeout=10, poll_frequency=1.0)
        # 動的なHTML生成を待つ
        modal_body = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "title")))
        
        html = driver.page_source
        await asyncio.sleep(5)
        part_soup = BeautifulSoup(html, 'html.parser')
        part_img_url = part_soup.find('img', id='modalThumbImg')['data-src']
        
        # URLが1_3.pngになってたら、1_1.pngに置換
        if part_img_url and "1_3.png" in part_img_url:
            part_img_url = part_img_url.replace("1_3.png", "1_1.png")

        return {
            "work_id": str(work_id),
            "work_title": work_title,
            "work_thumbnail_url": src_url if 'src_url' in locals() else None,
            "latest_part_id": latest_part_id,
            "latest_part_title": latest_part_title,
            "latest_part_thumbnail_url": part_img_url if 'part_img_url' in locals() else None,
            "latest_update_date": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schedule_day": schedule_day,
            "schedule_time": schedule_time,
        }
    except urllib3.exceptions.ReadTimeoutError:
        print(f"タイムアウトエラー: {work_title}: 第{latest_part_id}話の更新確認をスキップします.")
    except Exception as e:
        print(f"エラー: {work_title}: 第{latest_part_id}話の更新確認をスキップします.")
    finally: 
        driver.quit()
    


async def search_anime(query: str) -> (list):
    """
    アニメを検索し、Embedと[(work_id, title), ...]を返す
    """
    url = f"https://animestore.docomo.ne.jp/animestore/sch_pc?searchKey={query}&vodTypeList=svod_tvod&sortKey=4"
    # Selenium用のドライバをセットアップ
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # ヘッドレスモード（ブラウザを表示しない）
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