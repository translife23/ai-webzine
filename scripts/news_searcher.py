"""
WebSearch 기반 뉴스 검색 — 토픽당 해외 1건 + 국내 1건 (총 22건)

각 토픽별로 화제성 높은 기사를 검색한다.
- 해외: 영문 trending/viral 쿼리
- 국내: 한국어 최신 뉴스 쿼리
번역은 Routine A (Claude Code 세션)가 처리한다.
"""

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
    origin: str          # "해외" | "국내"
    relevance_score: float = 0.0
    title_ko: str = ""
    summary_ko: str = ""


# 토픽별 해외/국내 검색 쿼리
TOPIC_QUERIES: dict[str, dict] = {
    "화폐금융": {
        "keywords": ["AI", "fintech", "CBDC", "central bank", "digital currency", "payment", "monetary"],
        "foreign_query": "AI fintech CBDC digital currency payment trending news 2026",
        "domestic_query": "AI 핀테크 디지털화폐 중앙은행 결제 최신 뉴스 2026",
    },
    "금융투자": {
        "keywords": ["AI", "algorithmic trading", "investment", "hedge fund", "quantitative", "asset management"],
        "foreign_query": "AI algorithmic trading investment hedge fund trending news 2026",
        "domestic_query": "AI 알고리즘 트레이딩 투자 자산운용 최신 뉴스 2026",
    },
    "로봇": {
        "keywords": ["robot", "humanoid", "automation", "autonomous", "Boston Dynamics", "Figure"],
        "foreign_query": "AI humanoid robot automation trending viral news 2026",
        "domestic_query": "AI 휴머노이드 로봇 자동화 국내 최신 뉴스 2026",
    },
    "에너지": {
        "keywords": ["AI", "data center", "power", "nuclear", "energy", "electricity", "grid"],
        "foreign_query": "AI data center energy power consumption nuclear trending news 2026",
        "domestic_query": "AI 데이터센터 전력 에너지 원전 국내 최신 뉴스 2026",
    },
    "방산": {
        "keywords": ["AI", "defense", "military", "autonomous weapon", "drone", "cyber warfare"],
        "foreign_query": "AI defense military autonomous weapons drone trending news 2026",
        "domestic_query": "AI 방산 자율무기 드론 사이버전 K방산 최신 뉴스 2026",
    },
    "헬스케어·바이오": {
        "keywords": ["AI", "drug", "biotech", "healthcare", "medical", "diagnosis", "clinical"],
        "foreign_query": "AI drug discovery healthcare biotech diagnosis trending news 2026",
        "domestic_query": "AI 신약개발 헬스케어 바이오 의료 진단 국내 최신 뉴스 2026",
    },
    "반도체·HW인프라": {
        "keywords": ["chip", "GPU", "semiconductor", "NVIDIA", "HBM", "NPU", "datacenter"],
        "foreign_query": "AI chip GPU semiconductor NVIDIA HBM trending news 2026",
        "domestic_query": "AI 반도체 GPU 칩 HBM 국내 최신 뉴스 2026",
    },
    "농업·푸드테크": {
        "keywords": ["AI", "agriculture", "food", "farming", "crop", "agtech", "foodtech"],
        "foreign_query": "AI agriculture food tech precision farming trending news 2026",
        "domestic_query": "AI 정밀농업 푸드테크 대체식품 국내 최신 뉴스 2026",
    },
    "제조·스마트팩토리": {
        "keywords": ["AI", "manufacturing", "factory", "digital twin", "predictive maintenance"],
        "foreign_query": "AI smart manufacturing digital twin factory automation trending news 2026",
        "domestic_query": "AI 스마트팩토리 디지털트윈 제조혁신 국내 최신 뉴스 2026",
    },
    "AI거버넌스·규제": {
        "keywords": ["AI regulation", "EU AI Act", "AI governance", "AI law", "AI policy", "AI safety"],
        "foreign_query": "AI regulation EU AI Act governance policy law trending news 2026",
        "domestic_query": "AI 규제 AI기본법 AI거버넌스 정책 국내 최신 뉴스 2026",
    },
    "항공우주·SAF": {
        "keywords": ["AI", "space", "satellite", "UAM", "aviation", "SpaceX", "sustainable aviation"],
        "foreign_query": "AI space satellite UAM aviation SpaceX trending news 2026",
        "domestic_query": "AI 우주 위성 UAM 항공 지속가능항공유 국내 최신 뉴스 2026",
    },
}


def search_topic(topic_tag: str) -> list[Article]:
    """
    토픽별 해외 1건 + 국내 1건 반환.
    실제 검색은 Claude Code 세션(WebSearch 도구)이 수행한다.
    이 함수는 쿼리 정보만 제공하며, Routine A 지침에서 Claude가 직접 검색한다.
    """
    config = TOPIC_QUERIES.get(topic_tag, {})
    return []  # Claude WebSearch가 직접 처리


def get_search_plan() -> list[dict]:
    """Routine A 지침용 검색 계획 반환"""
    plan = []
    for topic, cfg in TOPIC_QUERIES.items():
        plan.append({
            "topic": topic,
            "foreign_query": cfg["foreign_query"],
            "domestic_query": cfg["domestic_query"],
        })
    return plan
