# -*- coding: utf-8 -*-
"""개요 — 한 장으로 보는 Water Co-Scientist"""
import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import ui

tr = D.trends()
rows = D.inst_table(tr)
full = D.years_full(tr)
base = D.baseline(tr)
kws = D.keyword_table(tr)
assets = D.assets()
asset_total = sum(i.get("count", 0) for i in assets.get("items", []))
oa = D.oa_rising()
kk = D.kci_kwater()
ki = D.kci_inst()
n_kw = sum(len(r["keywords"]) for r in rows)
a, b = (full[0], full[-1]) if full else ("", "")

WAVES = """<svg class="waves" viewBox="0 0 1200 300" preserveAspectRatio="none" aria-hidden="true">""" + "".join(
    f'<path d="M0 {170 + k * 18} C 200 {120 + k * 18}, 400 {220 + k * 18}, 600 {170 + k * 18} S 1000 {120 + k * 18}, 1200 {170 + k * 18}" '
    f'fill="none" stroke="rgba(103,232,249,{0.05 + k * 0.02:.2f})" stroke-width="1.2"/>' for k in range(7)) + "</svg>"

ui.h(f"""
<div class="hero">{WAVES}<div class="in">
  <div>
    <div class="eb">Water Co-Scientist · R&amp;D Agent Platform</div>
    <h1>물 분야 R&amp;D 데이터<br><span>수집·분석 에이전트</span></h1>
    <p>해외 논문·국내 학회지·특허·K-water 연구보고서를 자동으로 수집·분석해 7개 연구소 분야별 연구 동향을 보여 줍니다.
    수집·라벨링·분석은 정해진 일정에 따라 자동 실행되고, 판정은 연구소 전문가가 합니다.</p>
  </div>
  <div class="facts">
    <div class="f"><b>{asset_total:,}</b><span>통합 물 지식 자산 (보고서·논문·특허)</span></div>
    <div class="f"><b>{oa.get("documents", 0):,}</b><span>핵심 12개 저널 논문 분석</span></div>
    <div class="f"><b>{(oa.get("labels") or {}).get("Rising", 0):,}</b><span>통계적으로 유의한 상승 용어</span></div>
    <div class="f"><b>7 <small style="font-size:.9rem;color:#94a3b8">× {n_kw}</small></b><span>연구소 × 추적 키워드</span></div>
  </div>
</div></div>""")

tot_series = [sum(r["series"][i] for r in rows) for i in range(len(full))] if rows else []
w_top = None
if rows:
    num = sum((r["top10"] or 0) * sum(r["series"]) for r in rows if r["top10"] is not None)
    den = sum(sum(r["series"]) for r in rows if r["top10"] is not None)
    w_top = num / den if den else None
fast = max(rows, key=lambda r: r["growth"] or -1e9) if rows else None
kby = kk.get("by_year") or {}
k_years = [y for y in sorted(kby) if int(y) < int(b or 9999)][-10:]
ui.kpis([
    {"label": f"연구소 관련 해외 논문 ({b})", "value": f"{tot_series[-1]:,}" if tot_series else "–", "unit": "편",
     "delta": ui.fmt_pct(D.pct(tot_series[0], tot_series[-1])) if tot_series else None, "up": True,
     "sub": f"{a}→{b} · 해외 전체 {ui.fmt_pct(base['growth'])}", "spark": tot_series, "color": ui.ACCENT},
    {"label": "성장률 1위 분야", "value": fast["name"] if fast else "–",
     "delta": ui.fmt_pct(fast["growth"]) if fast else None, "up": True, "sub": f"{a}→{b} 논문 수",
     "spark": fast["series"] if fast else None, "color": ui.INST_COLORS.get(fast["code"]) if fast else ui.ACCENT},
    {"label": "피인용 상위 10% 비중", "value": f"{w_top:.1f}" if w_top else "–", "unit": "%",
     "delta": f"{w_top / base['top10']:.1f}배" if w_top and base["top10"] else None, "up": True,
     "sub": f"해외 전체 {base['top10']:.1f}% 대비" if base["top10"] else "", "color": "#9085e9"},
    {"label": "K-water 국내 학회지 논문", "value": f"{kk.get('total', 0):,}", "unit": "편", "sub": "KCI · 2001~",
     "spark": [kby.get(y, 0) for y in k_years], "color": "#d95926"},
    {"label": "상승 용어 군집", "value": f"{(oa.get('run') or {}).get('clusters', 0)}", "unit": "개",
     "sub": f"용어 {(oa.get('labels') or {}).get('Rising', 0):,}개 · Mann-Kendall + FDR", "color": "#199e70"},
])

c1, c2 = st.columns([2, 1], gap="medium")
with c1:
    with ui.card("growth", f"연구소별 해외 논문 성장 지수 ({a} = 100)", "OpenAlex 실측 · 연구소 키워드 전체의 연도별 논문 수", "Global"):
        fig = go.Figure()
        if base["series"] and base["series"][0]:
            fig.add_trace(go.Scatter(x=full, y=[v / base["series"][0] * 100 for v in base["series"]], name="해외 전체",
                                     line=dict(color="#94a3b8", width=2, dash="dot"), hovertemplate="해외 전체 %{x} · %{y:.0f}<extra></extra>"))
        for r in rows:
            if not r["series"][0]:
                continue
            fig.add_trace(go.Scatter(x=full, y=[v / r["series"][0] * 100 for v in r["series"]], name=r["name"], mode="lines+markers",
                                     line=dict(color=ui.INST_COLORS[r["code"]], width=2.4, shape="spline"), marker=dict(size=6),
                                     hovertemplate=r["name"] + " %{x} · %{y:.0f}<extra></extra>"))
        ui.style(fig, 340)
        fig.update_xaxes(type="category")
        ui.plot(fig, "ov_growth")
with c2:
    with ui.card("board", "연구소별 성장률", f"{a}→{b} 성장 · 괄호는 피인용 상위 10% 비중", "7 Institutes"):
        rr = sorted(rows, key=lambda r: -(r["growth"] or 0))
        ui.ranked([{"label": r["name"], "value": r["growth"] or 0, "color": ui.INST_COLORS[r["code"]],
                    "sub": f"{r['last']:,}편" + (f" · {r['top10']:.1f}%" if r["top10"] is not None else "")} for r in rr],
                  fmt="{:+.0f}%")

d1, d2, d3 = st.columns(3, gap="medium")
with d1:
    with ui.card("fastkw", "성장률 상위 키워드", f"{a}→{b} 논문 수 증가 · 연간 100편 이상", "Growth"):
        top = sorted([k for k in kws if k["last"] >= 100 and k["growth"] is not None], key=lambda k: -k["growth"])[:6]
        ui.ranked([{"label": k["kw"], "sub": k["inst"], "value": k["growth"], "color": ui.INST_COLORS[k["code"]]} for k in top],
                  fmt="{:+.0f}%")
with d2:
    with ui.card("citekw", "피인용 상위 10% 비중 상위 키워드", "피인용 상위 10% 논문 비중 · 4년 300편 이상", "Impact"):
        top = sorted([k for k in kws if k["n"] >= 300 and k["top10"] is not None], key=lambda k: -k["top10"])[:6]
        ui.ranked([{"label": k["kw"], "sub": k["inst"], "value": k["top10"], "color": ui.INST_COLORS[k["code"]]} for k in top])
with d3:
    with ui.card("kwspec", "K-water 특화도 상위 분야", "국내 학회지 대비 K-water 논문 비중 (KCI 최근 5년)", "Korea"):
        sc = ki.get("scopes") or {}
        dom, kw = sc.get("domestic") or {}, sc.get("kwater") or {}
        spec = []
        for c in D.INST_ORDER:
            dn = (dom.get("inst", {}).get(c) or {}).get("n", 0)
            kn = (kw.get("inst", {}).get(c) or {}).get("n", 0)
            if dn and dom.get("N") and kw.get("N"):
                spec.append({"label": D.INST_SHORT[c], "value": (kn / kw["N"]) / (dn / dom["N"]),
                             "sub": f"{kn}편", "color": ui.INST_COLORS[c]})
        ui.ranked(sorted(spec, key=lambda r: -r["value"])[:6], fmt="{:.2f}배")

with ui.card("flow", "처리 흐름", "수집·라벨링·분석은 자동 실행, 판정은 연구소 전문가", "Pipeline"):
    steps = [("01", "수집", f"OpenAlex·KCI·ALIO·KIPRIS를 6시간·매일 자동 수집 — 핵심 저널 {oa.get('documents', 0):,}편"),
             ("02", "정제·라벨", "초록 보강 → LLM이 대상·문제·도메인 라벨, K-water 소속 판정"),
             ("03", "분석", "추세검정(Mann-Kendall)·FDR·공출현 네트워크로 떠오르는 주제 탐지"),
             ("04", "사람 검토", "연구소 전문가가 라벨·배정을 판정(HITL) — 판정 기록이 다음 학습 재료"),
             ("05", "활용", "관제센터·지식노트·기술 지도에서 조회")]
    ui.h('<div class="flow">' + "".join(f'<div class="st"><div class="i">{i}</div><b>{t}</b><span>{s}</span></div>'
                                           for i, t, s in steps) + "</div>")
