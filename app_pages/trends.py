# -*- coding: utf-8 -*-
"""세계 연구 흐름 — 7개 연구소 관련 해외 논문 (OpenAlex)"""
import math

import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import ui

tr = D.trends()
rows = D.inst_table(tr)
full = D.years_full(tr)
base = D.baseline(tr)
kws = D.keyword_table(tr)
a, b = (full[0], full[-1]) if full else ("", "")

ui.page_header("Global research trends", "세계 연구 흐름",
               f"전 세계 학술 논문 데이터베이스 OpenAlex에서 7개 연구소 키워드가 제목·초록에 들어간 논문을 해마다 셉니다. "
               f"같은 기간 해외 전체 논문은 {ui.fmt_pct(base['growth'])} 늘었으니, 이보다 빠르면 특히 뜨는 분야입니다.",
               [f"기간 <b>{a}–{b}</b>", f"키워드 <b>{len(kws)}</b>", f"갱신 <b>{D.updated_label()}</b>"])

ui.kpis([{"label": r["name"], "value": f"{r['last']:,}", "unit": "편", "delta": ui.fmt_pct(r["growth"]),
          "up": (r["vs_base"] or 0) >= 0, "sub": f"해외 대비 {r['vs_base']:+.0f}%p" if r["vs_base"] is not None else "",
          "spark": r["series"], "color": ui.INST_COLORS[r["code"]]} for r in rows])

c1, c2 = st.columns([3, 2], gap="medium")
with c1:
    with ui.card("lines", "연구소 관련 논문 — 연도별", "실선 = 연구소 키워드 전체(합집합) 논문 수", "Volume"):
        mode = st.segmented_control("보기", ["편수", f"성장 지수 ({a}=100)"], default="편수", key="tr_mode",
                                    label_visibility="collapsed")
        fig = go.Figure()
        idx = mode != "편수"
        if idx and base["series"] and base["series"][0]:
            fig.add_trace(go.Scatter(x=full, y=[v / base["series"][0] * 100 for v in base["series"]], name="해외 전체",
                                     line=dict(color="#94a3b8", width=2, dash="dot")))
        for r in rows:
            y = [v / r["series"][0] * 100 for v in r["series"]] if idx and r["series"][0] else r["series"]
            fig.add_trace(go.Scatter(x=full, y=y, name=r["name"], mode="lines+markers",
                                     line=dict(color=ui.INST_COLORS[r["code"]], width=2.4, shape="spline"), marker=dict(size=6),
                                     hovertemplate=r["name"] + " %{x} · %{y:,.0f}<extra></extra>"))
        ui.style(fig, 360)
        fig.update_xaxes(type="category")
        ui.plot(fig, "tr_lines")
with c2:
    with ui.card("bubble", "성장 × 피인용 — 어디가 크면서 영향력도 있나", "가로 = 해외 대비 성장(%p) · 세로 = 피인용 상위 10% 비중 · 크기 = 편수", "Position"):
        pts = [r for r in rows if r["top10"] is not None and r["vs_base"] is not None]
        mx = max([r["last"] for r in pts] or [1])
        fig = go.Figure(go.Scatter(
            x=[r["vs_base"] for r in pts], y=[r["top10"] for r in pts], mode="markers+text",
            text=[r["name"] for r in pts], textposition="top center", textfont=dict(color="#e2e8f0", size=11),
            marker=dict(size=[14 + 30 * math.sqrt(r["last"] / mx) for r in pts], color=[ui.INST_COLORS[r["code"]] for r in pts],
                        opacity=.88, line=dict(color="#0b1222", width=2)),
            customdata=[[r["growth"], r["last"]] for r in pts],
            hovertemplate="<b>%{text}</b><br>해외 대비 %{x:+.0f}%p (성장 %{customdata[0]:+.0f}%)<br>피인용 상위 10% %{y:.1f}%<br>%{customdata[1]:,}편<extra></extra>"))
        fig.add_vline(x=0, line=dict(color="rgba(148,163,184,.35)", width=1))
        if base["top10"]:
            fig.add_hline(y=base["top10"], line=dict(color="rgba(148,163,184,.5)", width=1, dash="dot"),
                          annotation_text=f"해외 전체 {base['top10']:.1f}%", annotation_position="bottom right",
                          annotation_font=dict(color="#94a3b8", size=10))
        ui.style(fig, 360, legend=False)
        fig.update_xaxes(ticksuffix="%p")
        fig.update_yaxes(ticksuffix="%")
        ui.plot(fig, "tr_bubble")

with ui.card("kwexp", "키워드 탐색 — 연구소 안에서 어떤 세부 주제가 오르나", "연구소를 고르면 키워드별 추이와 성장·피인용이 나옵니다", "Keywords"):
    pick = st.segmented_control("연구소", D.INST_ORDER, format_func=lambda c: D.INST_SHORT[c], default="INST-07",
                                key="tr_inst", label_visibility="collapsed") or "INST-07"
    sub = [k for k in kws if k["code"] == pick]
    k1, k2 = st.columns([3, 2], gap="medium")
    with k1:
        fig = go.Figure()
        pal = ["#22d3ee", "#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9"]
        for i, k in enumerate(sorted(sub, key=lambda k: -k["last"])):
            fig.add_trace(go.Scatter(x=full, y=k["series"], name=k["kw"], mode="lines+markers",
                                     line=dict(color=pal[i % len(pal)], width=2.2, shape="spline"), marker=dict(size=5),
                                     hovertemplate=k["kw"] + " %{x} · %{y:,}편<extra></extra>"))
        ui.style(fig, 330)
        fig.update_xaxes(type="category")
        ui.plot(fig, "tr_kwlines")
    with k2:
        ss = sorted(sub, key=lambda k: -(k["growth"] or -1e9))
        ui.ranked([{"label": k["kw"], "value": k["growth"] or 0,
                    "sub": (f"피인용 {k['top10']:.1f}%" if k["top10"] is not None else "") + f" · {k['last']:,}편",
                    "color": ui.INST_COLORS[pick]} for k in ss], fmt="{:+.0f}%")
        ui.note(f"{a}→{b} 논문 수 증가율 · 키워드끼리 겹치는 논문이 있음")

with ui.card("kwboard", "전체 키워드 순위 — 성장과 영향력", f"7개 연구소 {len(kws)}개 키워드 · 막대 = {a}→{b} 성장, 점 = 피인용 상위 10% 비중", "Leaderboard"):
    top = sorted([k for k in kws if k["growth"] is not None and k["last"] >= 50], key=lambda k: -k["growth"])[:18][::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=[f"{k['kw']}  ·  {k['inst']}" for k in top], x=[k["growth"] for k in top], orientation="h", name="성장",
                         marker=dict(color=[ui.INST_COLORS[k["code"]] for k in top], cornerradius=4),
                         hovertemplate="%{y}<br>성장 %{x:+.0f}%<extra></extra>"))
    if base["growth"] is not None:
        fig.add_vline(x=base["growth"], line=dict(color="rgba(148,163,184,.6)", width=1.2, dash="dot"),
                      annotation_text=f"해외 전체 {base['growth']:+.0f}%", annotation_font=dict(color="#94a3b8", size=10))
    ui.style(fig, 560, legend=False, margin=dict(l=8, r=20, t=24, b=8))
    fig.update_xaxes(ticksuffix="%")
    ui.plot(fig, "tr_board")
    ui.note("연간 50편 이상인 키워드 중 성장 상위 18개 · 색 = 연구소")
