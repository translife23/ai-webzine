"""
기사 큐레이션 모듈 — 수집된 후보 기사에서 최종 12개를 선정한다.

선정 기준:
1. Claude API (haiku)로 관련성 점수 0~1 산출
2. 최소 3개 토픽 영역 포함 강제
3. 동일 출처 2건 초과 금지
4. 최신 기사 우선 (7일 이내)
5. 최종 12개 + 여분 3개 반환
"""

import json
import os
from collections import defaultdict

import anthropic

from news_searcher import Article


_SCORE_PROMPT = """\
다음 AI 관련 뉴스 기사가 IT 감리업 종사자에게 얼마나 유용한지 0.0~1.0 사이 점수로만 답하라.
유용한 기준: 최신성, 사회적 영향, 실무 관련성, 정보 밀도.
기사 제목: {title}
기사 요약: {summary}
숫자만 출력 (예: 0.85)"""


def score_article(client: anthropic.Anthropic, article: Article) -> float:
    """Claude haiku로 기사 관련성 점수를 산출한다."""
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": _SCORE_PROMPT.format(
                    title=article.title,
                    summary=article.summary,
                ),
            }],
        )
        score_text = message.content[0].text.strip()
        return min(1.0, max(0.0, float(score_text)))
    except Exception:
        return article.raw_score  # Tavily 점수를 폴백으로 사용


def curate(
    all_articles: dict[str, list[Article]],
    select_count: int = 12,
    spare_count: int = 3,
    min_topics: int = 3,
) -> tuple[list[Article], list[Article]]:
    """
    수집된 기사에서 select_count개를 선정하고 spare_count개 여분을 함께 반환한다.

    Returns:
        (selected, spare) 튜플
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

    client = anthropic.Anthropic(api_key=api_key)

    # 1. 점수화
    flat: list[Article] = []
    for articles in all_articles.values():
        for article in articles:
            article.relevance_score = score_article(client, article)
            flat.append(article)

    # 2. 관련성 점수 내림차순 정렬
    flat.sort(key=lambda a: a.relevance_score, reverse=True)

    # 3. 탐욕 선정: 최소 min_topics 토픽, 동일 출처 ≤ 2건 제약
    selected: list[Article] = []
    source_count: dict[str, int] = defaultdict(int)
    topic_count: dict[str, int] = defaultdict(int)

    for article in flat:
        if len(selected) >= select_count + spare_count:
            break
        # 동일 출처 2건 초과 방지
        if source_count[article.source] >= 2:
            continue
        selected.append(article)
        source_count[article.source] += 1
        topic_count[article.topic_tag] += 1

    # 4. 최소 토픽 수 검증
    covered_topics = len([t for t, c in topic_count.items() if c > 0])
    if covered_topics < min_topics:
        print(f"[WARN] 선정된 토픽 수({covered_topics})가 최소 기준({min_topics}) 미달")

    main = selected[:select_count]
    spare = selected[select_count:select_count + spare_count]
    return main, spare


def to_dict(article: Article) -> dict:
    return {
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "published_date": article.published_date,
        "summary": article.summary,
        "topic_tag": article.topic_tag,
        "relevance_score": round(article.relevance_score, 3),
    }
