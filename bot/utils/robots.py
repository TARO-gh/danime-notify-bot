import time
from typing import Optional, Dict
from urllib.robotparser import RobotFileParser
from urllib.parse import urlsplit
import requests


class RobotsDisallowed(Exception):
    """robots.txt により対象URLの取得が許可されていないことを示す例外。"""

    def __init__(self, url: str):
        super().__init__(f"robots.txt disallows: {url}")
        self.url = url


class RobotsChecker:
    """
    robots.txt を TTL付きでキャッシュし、can_fetch() で許可判定する。

    - robots.txt 自体は JS 不要なので requests で取得（Selenium不要）。
    - robots.txt が変わっても TTL 経過後に自動で再取得する。
    - 取得失敗時はキャッシュを温存（あればそれを使う）。
      キャッシュが一度も無い場合は fail-open（許可）＋ログ。
    - 未取得時の再試行が過剰にならないよう、取得試行自体も間隔で制御する。
    """

    USER_AGENT = "*"

    def __init__(self, ttl_seconds: int = 6 * 3600, retry_seconds: int = 300, timeout: float = 10.0):
        self.ttl = ttl_seconds            # 取得済みキャッシュの有効期間
        self.retry = retry_seconds        # 未取得時の再試行間隔
        self.timeout = timeout
        self._parsers: Dict[str, RobotFileParser] = {}
        self._last_attempt: Dict[str, float] = {}

    def _robots_url(self, url: str) -> str:
        parts = urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}/robots.txt"

    def _refresh(self, robots_url: str) -> None:
        try:
            resp = requests.get(
                robots_url,
                timeout=self.timeout,
                headers={"User-Agent": "danime-notify-bot"},
            )
            resp.raise_for_status()
            parser = RobotFileParser()
            parser.parse(resp.text.splitlines())
            self._parsers[robots_url] = parser
            print(f"[robots] 取得成功: {robots_url}")
        except Exception as e:
            # 取得失敗: 既存キャッシュがあれば温存。無ければ can_fetch 側で fail-open。
            print(f"[robots] 取得失敗（キャッシュ優先/無ければfail-open）: {robots_url} "
                  f"({type(e).__name__}: {e})")

    def _get_parser(self, robots_url: str) -> Optional[RobotFileParser]:
        now = time.time()
        parser = self._parsers.get(robots_url)
        # キャッシュ有: TTL、キャッシュ無: retry 間隔で取得を試みる
        interval = self.ttl if parser is not None else self.retry
        if now - self._last_attempt.get(robots_url, 0.0) >= interval:
            self._last_attempt[robots_url] = now
            self._refresh(robots_url)
        return self._parsers.get(robots_url)

    def can_fetch(self, url: str) -> bool:
        parser = self._get_parser(self._robots_url(url))
        if parser is None:
            # robots.txt を一度も取得できていない → fail-open（許可）
            return True
        return parser.can_fetch(self.USER_AGENT, url)


# シングルトン
robots_checker = RobotsChecker()
