# -*- coding: utf-8 -*-
"""국내 · K-water — KCI(한국학술지인용색인) 집계"""
import math

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import ui

kk = D.kci_kwater()
ki = D.kci_inst()
kr = D.kci_rising()
sc = ki.get("scopes") or {}
dom, kw, kin = sc.get("domestic") or {}, sc.get("kwater") or {}, sc.get("kwater_in_domestic") or {}
yrs = ki.get("years") or []
span = f"{yrs[0]}–{yrs[-1]}" if yrs else ""
kby = kk.get("by_year") or {}
years_all = [y for y in sorted(kby) if int(y) <= int(yrs[-1] if yrs else 9999)]

ui.page_header("Korea · K-water", "국내 학회지와 K-water",
               "KCI에 실린 국내 학회지 논문과 K-water 소속 논문을 연구소 분야로 나눠 견줍니다. "
               "공개 화면에는 건수·비중 같은 집계만 싣습니다 (KCI(한국학술지인용색인) 데이터 활용).",
               [f"최근 <b>{span}</b>", f"국내 학회지 <b>{dom.get('N', 0):,}편</b>", f"K-water <b>{kw.get('N', 0):,}편</b>"])

occ = kin.get("N", 0) / dom["N"] * 100 if dom.get("N") else None
recent = [kby.get(y, 0) for y in yrs]
ui.kpis([
    {"label": "K-water 국내 학회지 논문 (누적)", "value": f"{kk.get('total', 0):,}", "unit": "편", "sub": "2001년부터 · KCI 전체 학회지",
     "spark": [kby.get(y, 0) for y in years_all[-15:]], "color": "#d95926"},
    {"label": f"최근 5년 ({span})", "value": f"{sum(recent):,}", "unit": "편", "sub": f"연평균 {sum(recent) / max(len(recent), 1):.0f}편",
     "spark": recent, "color": "#c98500"},
    {"label": "국내 수자원·토목 학회지 안 K-water 점유율", "value": f"{occ:.1f}" if occ is not None else "–", "unit": "%",
     "sub": f"{kin.get('N', 0)}/{dom.get('N', 0):,}편", "color": "#22d3ee"},
    {"label": "함께 쓴 기관", "value": f"{len(kk.get('partners') or [])}+", "unit": "곳",
     "sub": " · ".join(p[0] for p in (kk.get("partners") or [])[:3]), "color": "#9085e9"},
])

c1, c2 = st.columns([3, 2], gap="medium")
with c1:
    with ui.card("kwyear", "K-water 소속 국내 학회지 논문 — 연도별", "KCI 전체 학회지 · 사람 판정(HITL)으로 소속 확인", "Timeline"):
        ys = years_all
        fig = go.Figure(go.Bar(x=ys, y=[kby.get(y, 0) for y in ys], marker=dict(
            color=[("#d95926" if y in yrs else "rgba(217,89,38,.45)") for y in ys], cornerradius=4),
            hovertemplate="%{x}년 · %{y}편<extra></extra>"))
        ui.style(fig, 320, legend=False)
        fig.update_xaxes(type="category", tickangle=0, nticks=12)
        ui.plot(fig, "kr_year")
        ui.note("진한 막대 = 최근 5년 분석 창")
with c2:
    with ui.card("journals", "K-water가 많이 싣는 학회지", f"{span} · KCI", "Journals"):
        jr = (kw.get("journals") or kk.get("journals") or [])[:7]
        ui.ranked([{"label": j, "value": n, "color": "#d95926"} for j, n in jr], fmt="{:,}편")

rows = []
for c in D.INST_ORDER:
    dn = (dom.get("inst", {}).get(c) or {}).get("n", 0)
    kn = (kw.get("inst", {}).get(c) or {}).get("n", 0)
    inn = (kin.get("inst", {}).get(c) or {}).get("n", 0)
    ds = dn / dom["N"] * 100 if dom.get("N") else None
    ks = kn / kw["N"] * 100 if kw.get("N") else None
    rows.append({"code": c, "name": D.INST_SHORT[c], "dn": dn, "kn": kn, "ds": ds, "ks": ks, "inn": inn,
                 "rta": ks / ds if ds and ks is not None else None, "occ": inn / dn * 100 if dn else None})

d1, d2 = st.columns(2, gap="medium")
with d1:
    with ui.card("mix", "분야 구성 — 국내 학회지 vs K-water", f"전체 논문 중 그 분야 비중 · {span} · 한 논문이 여러 분야에 들 수 있음", "Mix"):
        rr = rows[::-1]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=[r["name"] for r in rr], x=[r["ds"] or 0 for r in rr], orientation="h", name="국내 학회지",
                             marker=dict(color="#475569", cornerradius=3), customdata=[r["dn"] for r in rr],
                             hovertemplate="국내 학회지 · %{y} %{x:.1f}% (%{customdata}편)<extra></extra>"))
        fig.add_trace(go.Bar(y=[r["name"] for r in rr], x=[r["ks"] or 0 for r in rr], orientation="h", name="K-water",
                             marker=dict(color="#22d3ee", cornerradius=3), customdata=[r["kn"] for r in rr],
                             hovertemplate="K-water · %{y} %{x:.1f}% (%{customdata}편)<extra></extra>"))
        ui.style(fig, 380)
        fig.update_layout(barmode="group", bargap=.3, bargroupgap=.08)
        fig.update_xaxes(ticksuffix="%")
        ui.plot(fig, "kr_mix")
with d2:
    with ui.card("rta", "K-water 특화도", "K-water 비중 ÷ 국내 학회지 비중 · 1보다 크면 K-water가 상대적으로 많이 냄", "Specialization"):
        rr = [r for r in rows if r["rta"] is not None][::-1]
        fig = go.Figure(go.Bar(y=[r["name"] for r in rr], x=[r["rta"] - 1 for r in rr], base=1, orientation="h",
                               marker=dict(color=[("#22d3ee" if r["rta"] >= 1 else "#d95926") for r in rr], cornerradius=3),
                               text=[f"{r['rta']:.2f}배" for r in rr], textposition="outside", textfont=dict(color="#e2e8f0"),
                               cliponaxis=False, hovertemplate="%{y} · %{text}<extra></extra>"))
        fig.add_vline(x=1, line=dict(color="rgba(226,232,240,.6)", width=1.2))
        ui.style(fig, 380, legend=False)
        fig.update_xaxes(range=[0, max([r["rta"] for r in rr] + [1]) * 1.2], ticksuffix="배")
        ui.plot(fig, "kr_rta")
        ui.note("국내 학회지 기준은 수자원·토목 두 학회지라 상하수도·에너지 분야는 크게 나오기 쉬움")

sj = (kr.get("scopes") or {}).get("J11+J12") or {}
e1, e2 = st.columns([2, 3], gap="medium")
with e1:
    with ui.card("bigram", "국내 학회지 상승 표현", "두 단어 표현 · 최근 3년 비중 ÷ 예전 비중 · 준포아송 추세검정 + FDR", "Rising"):
        bg = [r for r in (sj.get("bigram") or {}).get("rising", []) if not r.get("minor") and r.get("lift") is not None]
        top = sorted(bg, key=lambda r: -r["lift"])[:10]
        ui.ranked([{"label": r["term"], "value": r["lift"], "sub": f"최근 {r['recent_docs']}편", "color": "#22d3ee"} for r in top],
                  fmt="{:.1f}배")
with e2:
    with ui.card("net", "상승 용어 네트워크", f"국내 수자원·토목 학회지 · 최근 5년 함께 나온 상승 용어 · 색 = 군집(Louvain)", "Network"):
        net = sj.get("network") or {}

        @st.cache_data(show_spinner=False)
        def layout(nodes, edges):
            """가장 큰 연결 덩어리만, 무게 없이 Kamada-Kawai — 고르게 퍼짐 (spring은 강한 연결이 한가운데로 뭉침)"""
            g = nx.Graph()
            g.add_nodes_from(n for n, _ in nodes)
            g.add_edges_from((s_, t_) for s_, t_, _ in edges)
            core = max(nx.connected_components(g), key=len)
            return nx.kamada_kawai_layout(g.subgraph(core))

        nodes = [(n["term"], n["df"]) for n in net.get("nodes", [])][:55]
        keep = {n for n, _ in nodes}
        edges = sorted([e for e in net.get("edges", []) if e[0] in keep and e[1] in keep], key=lambda e: -e[2])[:220]
        pos = layout(tuple(nodes), tuple(map(tuple, edges))) if nodes and edges else {}
        nodes = [(n, df) for n, df in nodes if n in pos]
        edges = [e for e in edges if e[0] in pos and e[1] in pos]
        if nodes and edges:
            comm = {}
            for c in net.get("communities", []):
                for t in c["terms"]:
                    comm.setdefault(t, c["id"])
            pal = ["#22d3ee", "#d95926", "#199e70", "#c98500", "#d55181", "#9085e9", "#3987e5"]
            fig = go.Figure()
            wmax = max(e[2] for e in edges)
            for s, t, w in edges:
                fig.add_trace(go.Scatter(x=[pos[s][0], pos[t][0]], y=[pos[s][1], pos[t][1]], mode="lines", hoverinfo="skip",
                                         line=dict(color=f"rgba(148,163,184,{0.06 + 0.32 * w / wmax:.2f})", width=0.6 + 2.2 * w / wmax),
                                         showlegend=False))
            dmax = max(df for _, df in nodes)
            fig.add_trace(go.Scatter(
                x=[pos[n][0] for n, _ in nodes], y=[pos[n][1] for n, _ in nodes], mode="markers+text",
                text=[n if df >= dmax * 0.22 else "" for n, df in nodes], textposition="top center",
                textfont=dict(color="#e2e8f0", size=11), hovertext=[f"{n} · 최근 5년 {df}편" for n, df in nodes], hoverinfo="text",
                marker=dict(size=[8 + 26 * math.sqrt(df / dmax) for _, df in nodes],
                            color=[pal[comm.get(n, 0) % len(pal)] for n, _ in nodes], line=dict(color="#0b1222", width=1.5), opacity=.95),
                showlegend=False))
            ui.style(fig, 430, legend=False, margin=dict(l=0, r=0, t=0, b=0))
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
            ui.plot(fig, "kr_net")
