# -*- coding: utf-8 -*-
"""지식 자산 · 에이전트 — 무엇을 모았고 누가 일하나"""
import time

import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import ui

assets = D.assets()
items = [i for i in assets.get("items", []) if i.get("count")]
total = sum(i["count"] for i in items)
COL = {"reports": "#22d3ee", "papers": "#3987e5", "patents": "#d95926"}

ui.page_header("Knowledge assets · Agents", "지식 자산과 에이전트",
               "K-water가 쌓아 온 연구보고서와 외부 논문·특허를 한곳에서 찾는 통합 물 지식 자산 정보검색 시스템(WCS), "
               "그리고 이를 수집·분석하는 에이전트 현황입니다.",
               [f"기준 <b>{assets.get('as_of', '-')}</b>", f"에이전트 <b>{len(D.agents())}</b>"])

ui.kpis([{"label": "통합 물 지식 자산", "value": f"{total:,}", "unit": "건", "sub": "보고서 + 논문 + 특허", "color": ui.ACCENT}] + [
    {"label": i["label"], "value": f"{i['count']:,}", "unit": i.get("unit", "건"), "sub": f"전체의 {i['count'] / total * 100:.1f}%",
     "color": COL.get(i["key"], ui.ACCENT)} for i in items])

c1, c2 = st.columns([2, 3], gap="medium")
with c1:
    with ui.card("donut", "지식 자산 구성", assets.get("system", "WCS"), "Assets"):
        fig = go.Figure(go.Pie(labels=[i["label"] for i in items], values=[i["count"] for i in items], hole=.68, sort=False,
                               marker=dict(colors=[COL.get(i["key"], "#64748b") for i in items], line=dict(color="#0b1222", width=3)),
                               textinfo="none", hovertemplate="%{label} · %{value:,} · %{percent}<extra></extra>"))
        fig.add_annotation(text=f"<b>{total:,}</b><br><span style='font-size:12px;color:#94a3b8'>전체 건수</span>", showarrow=False,
                           font=dict(size=22, color="#f8fafc"))
        ui.style(fig, 330, legend=True, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_layout(legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"))
        ui.plot(fig, "pf_donut")
        ui.note("논문이 대부분이라, 보고서(K-water 자체 성과)와 특허는 오른쪽 숫자 타일로 함께 봅니다.")
with c2:
    with ui.card("agents", "에이전트 목록", "에이전트별 상태와 최근 실행 (실행 기록 기준)", "Agents"):
        st_map = {"idle": ("대기 · 정상", "#34d399"), "running": ("실행 중", "#22d3ee"), "standby": ("준비", "#c98500"),
                  "plan": ("설계 중", "#94a3b8"), "error": ("오류", "#f87171")}
        names = {"openalex_collector": "해외 논문 감시 (OpenAlex)", "oa_rising": "떠오르는 주제 분석", "alio_crawler": "공공기관 보고서 수집 (ALIO)",
                 "alio_parser": "데이터소스 추출 (LLM)", "normalizer": "정규화 · 인벤토리", "kipris_collector": "특허 수집 (KIPRIS)",
                 "ft_trainer": "자체 LLM 학습 (QLoRA)", "article_collector": "기사 · 위크시그널 수집",
                 "tech_map": "기술 지도 점수 (논문 × 실용화)"}
        cards = []
        for a in D.agents():
            lab, col = st_map.get(a.get("state"), (a.get("state", "-"), "#94a3b8"))
            last = a.get("last_run")
            when = time.strftime("%m-%d %H:%M", time.gmtime(last + 9 * 3600)) if isinstance(last, (int, float)) and last > 1e9 else ""
            cards.append(f'<div class="ag"><div class="top"><b>{ui.esc(names.get(a["id"], a["id"]))}</b>'
                         f'<span class="st" style="color:{col};background:{col}1f;border:1px solid {col}55">{lab}</span></div>'
                         f'<p>{ui.esc(str(a.get("summary", ""))[:110])}</p>'
                         + (f'<p style="color:#64748b;margin-top:4px">최근 실행 {when} KST</p>' if when else "") + "</div>")
        ui.h('<div class="agents">' + "".join(cards) + "</div>")

with ui.card("sources", "데이터 출처와 이용 원칙", "", "Sources"):
    src = [("OpenAlex", "전 세계 학술 논문 2.5억 편+ 공개 색인 (CC0) — 연구소 키워드별 연도 추이·피인용 상위 10%", "#3987e5"),
           ("KCI", "한국학술지인용색인 — 국내 학회지·K-water 소속 논문. 원문은 비공개 저장소에만, 공개 화면은 집계만", "#d95926"),
           ("WCS", "통합 물 지식 자산 정보검색 시스템 — K-water 연구보고서·논문·특허", "#22d3ee"),
           ("ALIO · KIPRIS", "공공기관 경영정보 공개 보고서 · 특허 정보 — 데이터소스·특허 수집", "#c98500")]
    ui.h('<div class="agents">' + "".join(
        f'<div class="ag"><div class="top"><b>{n}</b><span class="st" style="color:{c};background:{c}1f;border:1px solid {c}55">source</span></div>'
        f'<p>{ui.esc(t)}</p></div>' for n, t, c in src) + "</div>")
    ui.note("이 화면의 숫자는 물벗 R&amp;D 에이전트(newcave/water-tech-agent)가 공개한 집계를 실시간으로 읽습니다. "
            "개인 이름·원문은 싣지 않습니다.")
