# -*- coding: utf-8 -*-
"""떠오르는 주제 — 수자원 핵심 12개 저널 논문(2000~2025) 용어 추세 분석"""
import math

import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import ui

oa = D.oa_rising()
lab = oa.get("labels") or {}
run = oa.get("run") or {}
cl = [c for c in oa.get("clusters", []) if c.get("size", 0) >= 3]
yrs = oa.get("years") or [2000, 2025]
PAL = ["#22d3ee", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9", "#3987e5", "#e66767"]

ui.page_header("Emerging topics", "떠오르는 연구 주제",
               f"수자원 분야 핵심 12개 저널에 {yrs[0]}~{yrs[-1]}년 실린 논문 {oa.get('documents', 0):,}편의 제목 단어를 해마다 세어, "
               "꾸준히 늘어나는 용어를 통계로 골라내고(Mann-Kendall 추세검정 + FDR 보정) 함께 나오는 용어끼리 묶었습니다.",
               [f"논문 <b>{oa.get('documents', 0):,}</b>", f"군집 <b>{run.get('clusters', len(cl))}</b>",
                f"모듈러리티 <b>{run.get('modularity', 0):.2f}</b>"])

ui.kpis([
    {"label": "분석 논문", "value": f"{oa.get('documents', 0):,}", "unit": "편", "sub": f"{yrs[0]}–{yrs[-1]} · 12개 저널", "color": ui.ACCENT},
    {"label": "검정한 용어", "value": f"{oa.get('candidates', 0):,}", "unit": "개", "sub": "충분히 자주 나온 단어", "color": "#3987e5"},
    {"label": "떠오르는 용어", "value": f"{lab.get('Rising', 0):,}", "unit": "개", "sub": "유의하게 증가 (q<0.05)", "color": "#199e70"},
    {"label": "줄어드는 용어", "value": f"{lab.get('Declining', 0):,}", "unit": "개", "sub": "유의하게 감소", "color": "#d95926"},
    {"label": "새로 등장한 용어", "value": f"{sum(1 for r in oa.get('rising', []) if r.get('new'))}", "unit": "개",
     "sub": "2015년 이후 처음 등장", "color": "#d55181"},
])

c1, c2 = st.columns([3, 2], gap="medium")
with c1:
    with ui.card("tree", "떠오르는 용어 군집 지도", "넓이 = 군집 안 상승 용어 수 · 색이 진할수록 최근 비중이 많이 커진 군집", "Clusters"):
        labels = [f"{c['label']}" for c in cl]
        fig = go.Figure(go.Treemap(
            labels=labels, parents=[""] * len(cl), values=[c["size"] for c in cl],
            marker=dict(colors=[c.get("gain", 0) for c in cl], colorscale=[[0, "#0e3a4f"], [0.5, "#0e7490"], [1, "#22d3ee"]],
                        line=dict(color="#0b1222", width=3), pad=dict(t=4, l=4, r=4, b=4)),
            customdata=[[c["size"], c.get("share", 0), c.get("gain", 0), ", ".join(t["term"] for t in c.get("top", [])[:5])] for c in cl],
            texttemplate="<b>%{label}</b><br>%{customdata[0]}개 용어<br><span style='font-size:11px'>%{customdata[3]}</span>",
            hovertemplate="<b>%{label}</b><br>상승 용어 %{customdata[0]}개 · 비중 증가 %{customdata[2]:.1f}<br>%{customdata[3]}<extra></extra>",
            textfont=dict(color="#f8fafc", size=13), tiling=dict(pad=3)))
        ui.style(fig, 420, legend=False, margin=dict(l=0, r=0, t=0, b=0))
        ui.plot(fig, "em_tree")
with c2:
    with ui.card("cnet", "군집끼리의 연결", "선 굵기 = 두 군집 용어가 같은 논문에 함께 나온 정도", "Links"):
        ids = [c["cluster"] for c in cl]
        n = len(ids)
        pos = {cid: (math.cos(2 * math.pi * i / n - math.pi / 2), math.sin(2 * math.pi * i / n - math.pi / 2)) for i, cid in enumerate(ids)}
        links = [l for l in oa.get("links", []) if l[0] in pos and l[1] in pos]
        wmax = max([l[2] for l in links] or [1])
        fig = go.Figure()
        for s, t, w in links:
            fig.add_trace(go.Scatter(x=[pos[s][0], pos[t][0]], y=[pos[s][1], pos[t][1]], mode="lines", hoverinfo="skip", showlegend=False,
                                     line=dict(color=f"rgba(34,211,238,{0.08 + 0.5 * w / wmax:.2f})", width=0.8 + 9 * w / wmax)))
        smax = max(c["size"] for c in cl)
        fig.add_trace(go.Scatter(
            x=[pos[c["cluster"]][0] for c in cl], y=[pos[c["cluster"]][1] for c in cl], mode="markers+text",
            text=[c["label"].split("·")[0][:12] for c in cl], textposition="bottom center", textfont=dict(color="#e2e8f0", size=11),
            hovertext=[f"{c['label']} · {c['size']}개" for c in cl], hoverinfo="text", showlegend=False,
            marker=dict(size=[14 + 40 * math.sqrt(c["size"] / smax) for c in cl], color=[PAL[i % len(PAL)] for i in range(n)],
                        line=dict(color="#0b1222", width=2))))
        ui.style(fig, 420, legend=False, margin=dict(l=10, r=10, t=10, b=10))
        fig.update_xaxes(visible=False, range=[-1.5, 1.5])
        fig.update_yaxes(visible=False, range=[-1.45, 1.35], scaleanchor="x")
        ui.plot(fig, "em_cnet")

with ui.card("detail", "군집 들여다보기", "군집을 고르면 그 군집을 이루는 대표 용어가 나옵니다", "Drill-down"):
    pick = st.segmented_control("군집", [c["cluster"] for c in cl],
                                format_func=lambda i: next(c["label"] for c in cl if c["cluster"] == i).split("·")[0][:16],
                                default=cl[0]["cluster"] if cl else None, key="em_pick", label_visibility="collapsed")
    c = next((c for c in cl if c["cluster"] == pick), cl[0] if cl else None)
    if c:
        k1, k2 = st.columns([3, 2], gap="medium")
        with k1:
            top = c.get("top", [])[:14][::-1]
            fig = go.Figure(go.Bar(y=[t["term"] for t in top], x=[t["docs"] for t in top], orientation="h",
                                   marker=dict(color=[f"rgba(34,211,238,{0.35 + 0.65 * t.get('inside', 0):.2f})" for t in top], cornerradius=4),
                                   customdata=[t.get("inside", 0) * 100 for t in top],
                                   hovertemplate="%{y} · %{x:,}편 · 군집 안 공출현 %{customdata:.0f}%<extra></extra>"))
            ui.style(fig, 420, legend=False)
            ui.plot(fig, f"em_terms_{c['cluster']}")
        with k2:
            ui.h(f'<div class="kpis" style="grid-template-columns:1fr 1fr">'
                    f'<div class="kpi"><div class="l">상승 용어</div><div class="v">{c["size"]}<small>개</small></div></div>'
                    f'<div class="kpi"><div class="l">추세 τ</div><div class="v">{c.get("tau", 0):.2f}</div></div>'
                    f'<div class="kpi"><div class="l">최근 비중</div><div class="v">{c.get("share", 0):.1f}<small>%</small></div></div>'
                    f'<div class="kpi"><div class="l">비중 증가</div><div class="v">{c.get("gain", 0):.1f}<small>%p</small></div></div></div>')
            ui.note(f"<b style='color:#e2e8f0'>{c['label']}</b> — 막대 = 그 용어가 나온 논문 수, 진할수록 이 군집 안에서 함께 나온 비율이 높음. "
                    f"군집 이름은 연구자가 검토해 붙인 라벨({c.get('label_src', '')})")

e1, e2 = st.columns(2, gap="medium")
with e1:
    with ui.card("new", "새로 등장한 단어", "2015년 이후 처음 나와 빠르게 늘어난 용어 · 논문 수", "New"):
        new = sorted([r for r in oa.get("rising", []) if r.get("new")], key=lambda r: -r["docs"])[:10]
        ui.ranked([{"label": r["term"], "value": r["docs"], "sub": f"{r['first']}년 첫 등장", "color": "#d55181"} for r in new], fmt="{:,}편")
with e2:
    with ui.card("updown", "가장 뚜렷하게 오르내린 용어", "Sen 기울기(연간 비중 변화) 기준 · 위 6개 상승, 아래 6개 하강", "Trend"):
        up = sorted(oa.get("rising", []), key=lambda r: -r.get("sen", 0))[:6]
        dn = sorted(oa.get("declining", []), key=lambda r: r.get("sen", 0))[:6]
        items = up + dn[::-1]
        fig = go.Figure(go.Bar(y=[r["term"] for r in items][::-1], x=[r["sen"] for r in items][::-1], orientation="h",
                               marker=dict(color=[("#199e70" if r["sen"] > 0 else "#d95926") for r in items][::-1], cornerradius=3),
                               customdata=[r["docs"] for r in items][::-1],
                               hovertemplate="%{y} · 기울기 %{x:+.3f} · %{customdata:,}편<extra></extra>"))
        fig.add_vline(x=0, line=dict(color="rgba(226,232,240,.4)", width=1))
        ui.style(fig, 380, legend=False)
        ui.plot(fig, "em_updown")
