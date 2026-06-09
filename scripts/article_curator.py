"""
기사 큐레이션 — 토픽당 해외 1건 + 국내 1건 (총 22건, 여분 없음)
"""

from news_searcher import Article


def curate(
    all_articles: dict[str, list[Article]],
) -> list[Article]:
    """
    토픽별로 해외 1건 + 국내 1건을 선정한다.
    all_articles: {topic_tag: [Article, ...]}
    각 Article의 origin은 "해외" 또는 "국내"
    """
    selected: list[Article] = []

    for topic, articles in all_articles.items():
        foreign = [a for a in articles if a.origin == "해외"]
        domestic = [a for a in articles if a.origin == "국내"]

        if foreign:
            selected.append(foreign[0])
        else:
            print(f"[WARN] {topic}: 해외 기사 없음")

        if domestic:
            selected.append(domestic[0])
        else:
            print(f"[WARN] {topic}: 국내 기사 없음")

    return selected


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
        "origin": article.origin,
        "relevance_score": article.relevance_score,
    }
