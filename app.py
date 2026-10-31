# -*- coding: utf-8 -*-
"""Water Co-Scientist 쇼케이스 (water-tech-agent2) — v1.2 (수집 현황 추가)
물벗 R&D 에이전트(newcave/water-tech-agent)의 공개 집계를 홍보·시연용 대시보드로 보여 준다.
모양: Dash 대시보드처럼 — 고정 상단바 · 카드 그리드 · 지표 타일 · 다크 Plotly (wca/ui.py).
실행: streamlit run app.py"""
import streamlit as st

from wca import data as D
from wca import techmap as T
from wca import ui


def _fresh(*mods):
    """Streamlit Cloud가 새 코드를 받은 뒤에도 예전 보조 모듈을 쥐고 있는 일이 있어(물벗 2026-10-28 사례),
    처음 한 번, 그 뒤로는 파일이 바뀌면 다시 읽는다."""
    import importlib
    import os
    for m in mods:
        try:
            mt = os.path.getmtime(m.__file__)
            if getattr(m, "_mt", None) is None or mt > m._mt:
                importlib.reload(m)
                m._mt = mt
        except Exception:
            pass


_fresh(D, T, ui)

APP_VERSION = "v1.2 · 2026-11-01"

st.set_page_config(page_title="Water Co-Scientist", page_icon="💧", layout="wide", initial_sidebar_state="collapsed")
ui.inject()

PAGES = [
    st.Page("app_pages/overview.py", title="개요", icon=":material/space_dashboard:", default=True),
    st.Page("app_pages/ops.py", title="수집 현황", icon=":material/monitoring:", url_path="ops"),
    st.Page("app_pages/trends.py", title="세계 연구 흐름", icon=":material/public:", url_path="trends"),
    st.Page("app_pages/korea.py", title="국내 · K-water", icon=":material/flag:", url_path="korea"),
    st.Page("app_pages/emerging.py", title="떠오르는 주제", icon=":material/trending_up:", url_path="emerging"),
    st.Page("app_pages/techmap.py", title="기술 지도", icon=":material/grid_view:", url_path="techmap"),
    st.Page("app_pages/platform.py", title="지식 자산 · 에이전트", icon=":material/hub:", url_path="platform"),
]
current = st.navigation(PAGES, position="hidden")
ui.topbar(PAGES, current)
current.run()
ui.footer(f"{D.updated_label()} · {APP_VERSION}")
