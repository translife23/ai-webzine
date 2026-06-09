"""
기사 큐레이션 — Claude API 없이 휴리스틱 점수로 12개 선정

선정 기준:
1. 키워드 밀도 점수 (제목·요약)
2. 최신성 점수 (오늘 날짜 기준 가까울수록 높음)
3. 최소 3개 토픽 영역 포함 강제
4. 동일 출처 2건 초과 금지
5. 최종 12개 + 여분 3개 반환
"""

from collections import defaultdict
from datetime import datetime, timezone
from news_searcher import Article, TOPIC_FEEDS


def _recency_score(published_date: str) -> float:
    """발행일이 최근일수록 1.0, 7일 전이면 0.0"""
    if not published_date:
        return 0.5
    try:
        pub = datetime.strptime(published_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        days_old = (datetime.now(timezone.utc) - pub).days
        return max(0.0, 1.0 - days_old / 7.0)
    except Exception:
        return 0.5


def _keyword_density(text: str, keywords: list[str]) -> float:
    """키워드 등장 비율 (최대 1.0)"""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    matched = sum(1 for kw in keywords if kw.lower() in text_lower)
    return min(1.0, matched / max(1, len(keywords) * 0.3))


def score_article(article: Article) -> float:
    keywords = TOPIC_FEEDS.get(article.topic_tag, {}).get("keywords", [])
    text = article.title + " " + article.summary
    recency = _recency_score(article.published_date)
    density = _keyword_density(text, keywords)
    return round(recency * 0.5 + density * 0.5, 3)


def curate(
    all_articles: dict[str, list[Article]],
    select_count: int = 12,
    spare_count: int = 3,
    min_topics: int = 3,
) -> tuple[list[Article], list[Article]]:
    # 점수화
    flat: list[Article] = []
    for articles in all_articles.values():
        for article in articles:
            article.relevance_score = score_article(article)
            flat.append(article)

    flat.sort(key=lambda a: a.relevance_score, reverse=True)

    # 탐욕 선정: 동일 출처 ≤ 2건, 최소 min_topics 토픽 보장
    selected: list[Article] = []
    source_count: dict[str, int] = defaultdict(int)
    topic_count: dict[str, int] = defaultdict(int)

    for article in flat:
        if len(selected) >= select_count + spare_count:
            break
        if source_count[article.source] >= 2:
            continue
        selected.append(article)
        source_count[article.source] += 1
        topic_count[article.topic_tag] += 1

    covered = len([t for t in topic_count if topic_count[t] > 0])
    if covered < min_topics:
        print(f"[WARN] 토픽 커버리지 {covered}개 (최소 {min_topics}개 권장)")

    return selected[:select_count], selected[select_count:select_count + spare_count]


def to_dict(article: Article) -> dict:
    return {
        "title": article.title,
        "title_ko": article.title_ko,
        "url": article.url,
        "source": article.source,
        "published_date": article.published_date,
        "summary": article.summary,
        "summary_ko": article.summary_ko,
        "topic_tag": article.topic_tag,
        "relevance_score": article.relevance_score,
    }
