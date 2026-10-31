# Water Co-Scientist — 쇼케이스 (water-tech-agent2)

K-water연구원 AI연구소 **물벗 R&D 에이전트**(`newcave/water-tech-agent`)의 공개 집계를 홍보·시연용으로 보여 주는 Streamlit 앱.
모양은 Dash 대시보드처럼(고정 상단바 · 카드 그리드 · 지표 타일 · 다크 Plotly).

| 화면 | 내용 |
|---|---|
| 개요 | 히어로 · 핵심 지표 · 연구소 성장 지수 · 스코어보드 · 키워드 순위 · 동작 흐름 |
| 세계 연구 흐름 | 7개 연구소 관련 해외 논문(OpenAlex) 추이 · 성장 × 피인용 · 키워드 탐색 · 전체 순위 |
| 국내 · K-water | KCI 집계: K-water 논문 연도별 · 게재 학회지 · 분야 구성·특화도 · 상승 표현 · 용어 네트워크 |
| 떠오르는 주제 | 핵심 12개 저널 91,125편 용어 추세: 군집 지도 · 군집 연결 · 군집별 용어 · 새 단어 · 오르내림 |
| 지식 자산 · 에이전트 | WCS 구성 · 에이전트 함대 · 출처와 원칙 |

- 데이터: `water-tech-agent` main의 `data_seed/`를 30분 캐시로 실시간 읽고, 실패하면 `snapshot/`(같은 공개 집계 사본)을 씀
- 실행: `streamlit run app.py` · 배포: Streamlit Community Cloud, main · `app.py`
- 출처: OpenAlex(CC0) · KCI(한국학술지인용색인) 데이터 활용(집계만) · WCS
