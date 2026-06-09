"""
RSS 기반 뉴스 검색 — API 키 불필요

11개 토픽 영역별 RSS 피드를 파싱하여 최근 7일 내 기사를 수집한다.
번역은 Routine A (Claude Code 세션)가 처리한다.
"""

import time
import feedparser
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class Article:
    title: str
    url: str
    source: str
    published_date: str
    summary: str
    topic_tag: str
    relevance_score: float = 0.0
    title_ko: str = ""
    summary_ko: str = ""


# 토픽별 키워드 + RSS 피드 매핑
TOPIC_FEEDS: dict[str, dict] = {
    "화폐금융": {
        "keywords": ["AI", "fintech", "CBDC", "central bank", "digital currency", "payment", "monetary"],
        "feeds": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://venturebeat.com/feed/",
        ],
    },
    "금융투자": {
        "keywords": ["AI", "algorithmic trading", "investment", "hedge fund", "quantitative", "asset management"],
        "feeds": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://venturebeat.com/feed/",
        ],
    },
    "로봇": {
        "keywords": ["robot", "humanoid", "automation", "autonomous", "Boston Dynamics", "Figure", "bipedal"],
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://www.therobotreport.com/feed/",
            "https://venturebeat.com/feed/",
        ],
    },
    "에너지": {
        "keywords": ["AI", "data center", "power consumption", "nuclear", "energy", "electricity", "grid"],
        "feeds": [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://techcrunch.com/feed/",
            "https://venturebeat.com/feed/",
        ],
    },
    "방산": {
        "keywords": ["AI", "defense", "military", "autonomous weapon", "drone", "cyber warfare", "Pentagon"],
        "feeds": [
            "https://www.defensenews.com/rss/",
            "https://feeds.reuters.com/reuters/worldNews",
            "https://techcrunch.com/feed/",
        ],
    },
    "헬스케어·바이오": {
        "keywords": ["AI", "drug", "biotech", "healthcare", "medical", "diagnosis", "clinical trial", "pharma"],
        "feeds": [
            "https://www.statnews.com/feed/",
            "https://feeds.reuters.com/reuters/healthNews",
            "https://techcrunch.com/feed/",
        ],
    },
    "반도체·HW인프라": {
        "keywords": ["chip", "GPU", "semiconductor", "NVIDIA", "AMD", "HBM", "NPU", "datacenter", "wafer"],
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://venturebeat.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/index",
        ],
    },
    "농업·푸드테크": {
        "keywords": ["AI", "agriculture", "food", "farming", "crop", "agtech", "foodtech", "precision farming"],
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://venturebeat.com/feed/",
        ],
    },
    "제조·스마트팩토리": {
        "keywords": ["AI", "manufacturing", "factory", "digital twin", "predictive maintenance", "Industry 4.0"],
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://venturebeat.com/feed/",
            "https://feeds.reuters.com/reuters/businessNews",
        ],
    },
    "AI거버넌스·규제": {
        "keywords": ["AI regulation", "EU AI Act", "AI governance", "AI law", "AI policy", "AI safety", "AI ethics"],
        "feeds": [
            "https://techcrunch.com/feed/",
            "https://venturebeat.com/feed/",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.thenextweb.com/feed/",
        ],
    },
    "항공우주·SAF": {
        "keywords": ["AI", "space", "satellite", "UAM", "aviation", "SpaceX", "sustainable aviation", "SAF"],
        "feeds": [
            "https://spacenews.com/feed/",
            "https://techcrunch.com/feed/",
            "https://feeds.reuters.com/reuters/scienceNews",
        ],
    },
}


def _parse_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _is_recent(dt: Optional[datetime], days: int = 7) -> bool:
    if not dt:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def _keyword_match(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def search_topic(topic_tag: str, days_back: int = 7, max_per_feed: int = 5) -> list[Article]:
    config = TOPIC_FEEDS.get(topic_tag, {})
    keywords = config.get("keywords", [])
    feeds = config.get("feeds", [])

    seen_urls: set[str] = set()
    articles: list[Article] = []

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                if count >= max_per_feed:
                    break
                url = entry.get("link", "")
                if not url or url in seen_urls:
                    continue

                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", ""))[:600].strip()

                if not _keyword_match(title + " " + summary, keywords):
                    continue

                pub_date = _parse_date(entry)
                if not _is_recent(pub_date, days_back):
                    continue

                seen_urls.add(url)
                articles.append(Article(
                    title=title,
                    url=url,
                    source=feed.feed.get("title", feed_url)[:60],
                    published_date=pub_date.strftime("%Y-%m-%d") if pub_date else "",
                    summary=summary,
                    topic_tag=topic_tag,
                ))
                count += 1
        except Exception as e:
            print(f"[RSS] {feed_url} 오류: {e}")

        time.sleep(0.3)

    return articles


def search_all_topics(days_back: int = 7, max_per_topic: int = 5) -> dict[str, list[Article]]:
    result: dict[str, list[Article]] = {}
    for topic in TOPIC_FEEDS:
        print(f"[RSS] {topic} 수집 중...")
        articles = search_topic(topic, days_back=days_back, max_per_feed=max_per_topic)
        result[topic] = articles
        print(f"[RSS] {topic}: {len(articles)}건")
    return result


if __name__ == "__main__":
    all_articles = search_all_topics()
    total = sum(len(v) for v in all_articles.values())
    print(f"\n총 {total}건 수집")
    for topic, arts in all_articles.items():
        for a in arts[:2]:
            print(f"  [{a.topic_tag}] {a.title[:70]}")
