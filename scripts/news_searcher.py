"""
뉴스 검색 모듈 — Tavily API를 이용해 11개 토픽 영역별 최신 뉴스를 검색한다.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from tavily import TavilyClient

TOPIC_QUERIES: dict[str, str] = {
    "화폐금융":         "AI monetary policy central bank digital currency CBDC fintech payments",
    "금융투자":         "AI algorithmic trading hedge fund investment valuation financial regulation",
    "로봇":             "AI humanoid robot industrial automation logistics Boston Dynamics",
    "에너지":           "AI data center power consumption nuclear energy smart grid electricity",
    "방산":             "AI autonomous weapons cyber warfare defense military technology",
    "헬스케어·바이오":  "AI drug discovery diagnosis medical device FDA healthcare biotech",
    "반도체·HW인프라":  "AI chip GPU NPU HBM semiconductor TSMC Nvidia supply chain",
    "농업·푸드테크":    "AI precision agriculture alternative protein food security climate crop",
    "제조·스마트팩토리":"AI digital twin predictive maintenance autonomous manufacturing factory",
    "AI거버넌스·규제":  "AI regulation EU AI Act executive order governance ethics law compliance",
    "항공우주·SAF":     "AI space economy satellite UAM urban air mobility sustainable aviation fuel",
}

TOPIC_TAGS: list[str] = list(TOPIC_QUERIES.keys())


@dataclass
class Article:
    title: str
    url: str
    source: str
    published_date: str
    summary: str
    topic_tag: str
    relevance_score: float = 0.0
    raw_score: float = field(default=0.0, repr=False)


def search_topic(
    client: TavilyClient,
    topic: str,
    days_back: int = 7,
    max_results: int = 5,
) -> list[Article]:
    """단일 토픽 영역의 뉴스를 검색하여 Article 목록을 반환한다."""
    query = TOPIC_QUERIES[topic]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            topic="news",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False,
        )
    except Exception as exc:
        print(f"[WARN] {topic} 검색 실패: {exc}")
        return []

    articles: list[Article] = []
    for result in response.get("results", []):
        pub_date = result.get("published_date", "") or ""
        # 오래된 기사 필터링 (날짜 정보 있을 때만)
        if pub_date and pub_date < cutoff:
            continue
        articles.append(
            Article(
                title=result.get("title", "").strip(),
                url=result.get("url", ""),
                source=_extract_domain(result.get("url", "")),
                published_date=pub_date[:10] if pub_date else "",
                summary=(result.get("content", "") or "")[:200].strip(),
                topic_tag=topic,
                raw_score=result.get("score", 0.0),
            )
        )
    return articles


def search_all_topics(
    days_back: int = 7,
    max_per_topic: int = 5,
) -> dict[str, list[Article]]:
    """11개 토픽 전체를 검색하고 토픽명 → 기사 목록 딕셔너리를 반환한다."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise EnvironmentError("TAVILY_API_KEY 환경 변수가 설정되지 않았습니다.")

    client = TavilyClient(api_key=api_key)
    results: dict[str, list[Article]] = {}

    for topic in TOPIC_TAGS:
        print(f"  검색 중: {topic}")
        articles = search_topic(client, topic, days_back=days_back, max_results=max_per_topic)
        results[topic] = articles
        print(f"    → {len(articles)}건 수집")

    return results


def _extract_domain(url: str) -> str:
    """URL에서 도메인명만 추출한다."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.removeprefix("www.")
    except Exception:
        return url
