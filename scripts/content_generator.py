"""
콘텐츠 생성 모듈 — Claude API를 이용해 기획 보고서(5단 구조)를 생성한다.
"""

import os
import re
import anthropic


_REPORT_SYSTEM_PROMPT = """\
당신은 정보시스템 감리업 전문가를 위한 AI 동향 분석 리포트 작성 전문가입니다.
독자는 IT 감리사·정보보안 전문가 등 기술과 정책 모두에 익숙한 고급 독자입니다.
모든 내용은 사실에 근거하고, 출처를 명시하며, 균형 잡힌 시각으로 작성하십시오.
한국어로 작성하되 전문 용어는 영문 병기합니다.
"""

_REPORT_USER_PROMPT = """\
다음 기획 보고서를 5단 구조로 작성하라.

주제: {title}
핵심 아젠다: {agenda}
분석 관점: {perspective}

**필수 구성:**

## 1. 배경지식
핵심 개념 정의, 기술/정책 배경, IT 감리 관점에서의 의미 (300자 이상)

## 2. 최근 3년간 동향 (2023~2026)
연도별 주요 사건·발표·정책 변화, 통계 수치 및 출처 명시 (400자 이상)

## 3. 최근 주목받는 이유
현재 이 주제가 부각되는 맥락, 미디어 노출 현황, 사회적 관심 배경 (200자 이상)

## 4. 주요 쟁점
쟁점 2개 이상을 선정하고 각 쟁점별로 찬성/반대 논거를 각 2개 이상 제시하라.

### 쟁점 1: [구체적인 쟁점 제목]
**주장 A:** [논거 1] / [논거 2]
**주장 B:** [논거 1] / [논거 2]

### 쟁점 2: [구체적인 쟁점 제목]
**주장 A:** [논거 1] / [논거 2]
**주장 B:** [논거 1] / [논거 2]

## 5. 전망
### 단기 전망 (6개월 이내)
### 중기 전망 (1~3년)

작성 원칙:
- 최신 자료 우선 (2025~2026년 기사·보고서 활용)
- 한국 IT 감리 실무와의 연관성 명시
- 각 섹션 기준 분량 준수
- 출처 명시 (기관명, 발행 연도)
"""


def generate_theme_report(
    title: str,
    agenda: str,
    perspective: str,
    theme_area: str,
) -> str:
    """
    기획 보고서를 생성하여 Markdown 문자열로 반환한다.

    Args:
        title: 보고서 제목
        agenda: 핵심 아젠다
        perspective: 분석 관점
        theme_area: 7개 테마 영역 중 하나
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수가 필요합니다.")

    client = anthropic.Anthropic(api_key=api_key)

    header = f"# {title}\n\n**테마 영역:** {theme_area}  \n**분석 관점:** {perspective}\n\n---\n\n"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_REPORT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": _REPORT_USER_PROMPT.format(
                title=title,
                agenda=agenda,
                perspective=perspective,
            ),
        }],
    )

    body = message.content[0].text.strip()
    return header + body


def generate_newsletter_intro(
    week_id: str,
    tech_report_title: str,
    nontech_report_title: str,
    article_count: int,
    topics_covered: list[str],
) -> str:
    """뉴스레터 상단 인트로 문구를 생성한다."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY 환경 변수가 필요합니다.")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"AI 웹진 {week_id}호 뉴스레터 인트로 문구를 3문장 이내로 작성하라. "
                f"이번 주 기획 보고서: '{tech_report_title}', '{nontech_report_title}'. "
                f"커버된 AI 토픽 영역: {', '.join(topics_covered)}. "
                f"총 {article_count}건의 주요 뉴스. 간결하고 흥미롭게 한국어로."
            ),
        }],
    )
    return message.content[0].text.strip()
