import datetime as dt
from typing import Optional, Tuple, List

SEASONS = ["winter", "spring", "summer", "fall"]
SEASON_LABELS = {
    "winter": "冬",
    "spring": "春",
    "summer": "夏",
    "fall": "秋",
}


def get_current_season_and_year(now: Optional[dt.datetime] = None) -> Tuple[str, int]:
    if now is None:
        now = dt.datetime.now()
    month = now.month
    if 1 <= month <= 3:
        return "winter", now.year
    if 4 <= month <= 6:
        return "spring", now.year
    if 7 <= month <= 9:
        return "summer", now.year
    return "fall", now.year


def format_season_label(year: int, season: str) -> str:
    jp = SEASON_LABELS.get(season, season)
    return f"{year}年 {jp}"


def iter_recent_seasons(limit: int = 25, now: Optional[dt.datetime] = None) -> List[Tuple[int, str]]:
    season, year = get_current_season_and_year(now)
    seasons: List[Tuple[int, str]] = []
    idx = SEASONS.index(season)
    for _ in range(limit):
        seasons.append((year, SEASONS[idx]))
        idx -= 1
        if idx < 0:
            idx = len(SEASONS) - 1
            year -= 1
    return seasons
