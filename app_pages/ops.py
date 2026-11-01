# -*- coding: utf-8 -*-
"""에이전트 수집 현황 — 2026-07-12부터 쉬지 않고 돈 수집·분석 에이전트의 실제 작업 기록.
재료: 물벗 data 브랜치 live/ops/ops.json (agents/ops_stats.py가 매시 git 기록·Actions 실행 기록·파이프라인 로그에서 다시 셈)."""
import math
import time
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from wca import data as D
from wca import ui

KST = timezone(timedelta(hours=9))
AG_COL = {"collector": "#3987e5", "labels": "#199e70", "heartbeat": "#22d3ee", "kci": "#c98500", "tech_map": "#d55181",
          "oa_rising": "#9085e9", "hitl": "#d95926", "bot_other": "#94a3b8", "dev": "#475569"}
AG_ORDER = ["collector", "labels", "heartbeat", "kci", "tech_map", "oa_rising", "hitl", "bot_other"]
SCHEDULE = [("논문 수집", "openalex-collector", "7 * * * *"), ("수집 현황판", "ops-stats", "53 * * * *"),
            ("해외 트렌드 심박", "agents-heartbeat", "17 */6 * * *"), ("LLM 라벨링", "labels-pipeline", "53 */6 * * *"),
            ("기술 지도", "tech-map", "41 1,7,13,19 * * *"), ("KCI 수집", "kci-rising", "11 21 * * *"),
            ("KCI 건수", "kci-counts", "41 20 * * 0"), ("상승 주제 연동", "oa-rising", "23 22 * * 0")]

o = D.ops()
if not o:
    ui.page_header("Live operations", "에이전트 수집 현황", "현황 자료를 읽지 못했습니다. 잠시 뒤 다시 열어 주세요.")
    st.stop()
T = o.get("totals") or {}
now = time.time()


def ago(ts):
    s = max(0, now - (ts or now))
    return f"{s:.0f}초 전" if s < 60 else f"{s / 60:.0f}분 전" if s < 3600 else f"{s / 3600:.1f}시간 전" if s < 86400 else f"{s / 86400:.0f}일 전"


def dur(s):
    s = int(s or 0)
    return f"{s}s" if s < 60 else f"{s // 60}m{s % 60:02d}s" if s < 3600 else f"{s // 3600}h{(s % 3600) // 60:02d}m"


def _match(field: str, v: int) -> bool:
    for part in field.split(","):
        if part == "*":
            return True
        if part.startswith("*/"):
            if v % int(part[2:]) == 0:
                return True
        elif "-" in part:
            a, b = map(int, part.split("-"))
            if a <= v <= b:
                return True
        elif int(part) == v:
            return True
    return False


def next_run(cron: str):
    mi, hr, _, _, dw = cron.split()
    t = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    base = t.replace(minute=0)
    for k in range(0, 24 * 8):
        c = base + timedelta(hours=k)
        c = c.replace(minute=int(mi))
        if c <= t:
            continue
        if _match(hr, c.hour) and _match(dw, (c.weekday() + 1) % 7):
            return c.timestamp()
    return None


daily = o.get("daily") or []
growth = o.get("growth") or []
wfs = o.get("workflows") or {}
since = o.get("since", "")
last_run = max((r["ts"] for r in o.get("recent") or []), default=None)

ui.page_header("Live operations · Agents at work", "에이전트 수집 현황",
               f"{since}부터 수집·라벨링·분석 에이전트가 사람 손 없이 돌아간 실제 작업 기록입니다. "
               "모든 숫자는 저장소의 실행 기록(커밋·GitHub Actions·파이프라인 로그)에서 매시 다시 셉니다.",
               [f"가동 <b>{o.get('days_since', 0)}일째</b>", f"마지막 실행 <b>{ago(last_run)}</b>",
                f"현황 갱신 <b>{ago(o.get('updated'))}</b>"])


# ── 큰 숫자 ──
def weekly(vals):
    out, acc = [], 0
    for i, v in enumerate(vals):
        acc += v
        if i % 7 == 6:
            out.append(acc)
            acc = 0
    return out[-16:]


runs_w = weekly([d.get("r", 0) for d in daily])
min_w = weekly([d.get("rmin", 0) for d in daily])
com_w = weekly([sum(v for k, v in (d.get("c") or {}).items() if k != "dev") for d in daily])
ui.kpis([
    {"label": "에이전트 실행", "value": f"{T.get('runs', 0):,}", "unit": "회", "sub": f"워크플로 {T.get('workflows', 0)}종 · 주별 추이",
     "spark": runs_w, "color": ui.ACCENT},
    {"label": "누적 가동 시간", "value": f"{T.get('run_minutes', 0) / 60:,.0f}", "unit": "시간",
     "sub": f"{T.get('run_minutes', 0):,}분 · 클라우드 러너", "spark": min_w, "color": "#3b82f6"},
    {"label": "자동 기록 커밋", "value": f"{T.get('commits_bot', 0):,}", "unit": "건", "sub": f"개발 커밋 {T.get('commits_dev', 0):,}건 별도",
     "spark": com_w, "color": "#9085e9"},
    {"label": "수집 핵심 논문", "value": f"{T.get('papers_core', 0):,}", "unit": "편",
     "sub": f"목표 {T.get('papers_core_target', 0):,} 중 {T.get('papers_core', 0) / max(1, T.get('papers_core_target') or 1) * 100:.1f}%",
     "color": "#199e70"},
    {"label": "LLM 라벨링", "value": f"{T.get('assigned', 0) or 0:,}", "unit": "편", "sub": f"초록 확보 {T.get('abstract_ok', 0) or 0:,} · 파이프라인 {T.get('pipeline_runs', 0)}회",
     "spark": [g.get("assigned") or 0 for g in growth][-30:], "color": "#d55181"},
    {"label": "쌓인 데이터", "value": f"{T.get('data_mb', 0):,.0f}", "unit": "MB", "sub": "수집 원본·초록·라벨 (data 브랜치)", "color": "#c98500"},
])

# ── 활동 캘린더 + 다음 실행 ──
c1, c2 = st.columns([2.4, 1], gap="medium")
with c1:
    with ui.card("ops-cal", "에이전트 활동 캘린더", "칸 하나 = 하루 · 진할수록 그날 실행이 많았던 날 (KST)", "Activity"):
        days = {d["d"]: d for d in daily}
        if days:
            d0 = datetime.strptime(min(days), "%Y-%m-%d")
            d1 = datetime.now(KST).replace(tzinfo=None)
            start = d0 - timedelta(days=d0.weekday())
            weeks = (d1 - start).days // 7 + 1
            z = [[None] * weeks for _ in range(7)]
            txt = [[""] * weeks for _ in range(7)]
            xs = [(start + timedelta(weeks=w)).strftime("%m/%d") for w in range(weeks)]
            for w in range(weeks):
                for wd in range(7):
                    day = start + timedelta(weeks=w, days=wd)
                    if day < d0 or day > d1:
                        continue
                    key = day.strftime("%Y-%m-%d")
                    x = days.get(key, {})
                    cm = sum(v for k, v in (x.get("c") or {}).items() if k != "dev")
                    z[wd][w] = x.get("r", 0)
                    txt[wd][w] = f"{key} · 실행 {x.get('r', 0)}회 · {x.get('rmin', 0):.0f}분 · 자동 커밋 {cm}건"
            fig = go.Figure(go.Heatmap(z=z, x=xs, y=["월", "화", "수", "목", "금", "토", "일"], text=txt, hoverinfo="text",
                                       xgap=3, ygap=3, showscale=False,
                                       colorscale=[[0, "#0f1d33"], [0.15, "#0e3a4f"], [0.45, "#0e7490"], [0.75, "#06b6d4"], [1, "#a5f3fc"]]))
            ui.style(fig, 230, legend=False, margin=dict(l=8, r=8, t=8, b=8))
            fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11))
            fig.update_xaxes(showgrid=False, side="top", tickfont=dict(size=10), nticks=18)
            ui.plot(fig, "ops_cal")
            busiest = max(daily, key=lambda d: d.get("r", 0))
            act = sum(1 for d in daily if d.get("r", 0) > 0)
            ui.note(f"가장 바빴던 날 <b style='color:#e2e8f0'>{busiest['d']}</b> 실행 {busiest.get('r', 0)}회 · "
                    f"실행이 있었던 날 {act}일 / {o.get('days_since', 0)}일 · 하루 평균 {T.get('runs', 0) / max(1, act):.1f}회")
with c2:
    with ui.card("ops-next", "다음 예정 실행", "GitHub Actions 일정 · 몇 분 늦을 수 있음", "Schedule"):
        nx = sorted([(next_run(c), n, w) for n, w, c in SCHEDULE if next_run(c)])[:6]
        rows = []
        for t, n, w in nx:
            m = (t - now) / 60
            left = f"{m:.0f}분 뒤" if m < 90 else f"{m / 60:.1f}시간 뒤"
            when = datetime.fromtimestamp(t, KST).strftime("%m-%d %H:%M")
            rows.append(f'<div class="nx"><span class="dot"></span><b>{ui.esc(n)}</b><span class="w">{when}</span><span class="l">{left}</span></div>')
        ui.h('<div class="nxs">' + "".join(rows) + "</div>")

# ── 일자별 작업량 + 24시간 ──
d1c, d2c = st.columns([2.4, 1], gap="medium")
with d1c:
    with ui.card("ops-daily", "일자별 에이전트 작업", "막대 = 에이전트별 자동 기록 커밋 · 선 = 그날 실행에 쓴 시간(분)", "Daily"):
        xs = [d["d"] for d in daily]
        agents = o.get("agents") or {}
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        for k in AG_ORDER:
            ys = [(d.get("c") or {}).get(k, 0) for d in daily]
            if not any(ys):
                continue
            fig.add_trace(go.Bar(x=xs, y=ys, name=(agents.get(k) or {}).get("label", k), marker=dict(color=AG_COL[k], line_width=0),
                                 hovertemplate="%{x} · %{y}건<extra>" + (agents.get(k) or {}).get("label", k) + "</extra>"), secondary_y=False)
        fig.add_trace(go.Scatter(x=xs, y=[d.get("rmin", 0) for d in daily], name="실행 시간(분)", mode="lines",
                                 line=dict(color="#fde047", width=1.6), hovertemplate="%{x} · %{y:.0f}분<extra></extra>"),
                      secondary_y=True)
        ui.style(fig, 340, margin=dict(l=8, r=8, t=40, b=8))
        fig.update_layout(barmode="stack", bargap=0.15)
        fig.update_yaxes(title="커밋", secondary_y=False)
        fig.update_yaxes(title="분", secondary_y=True, showgrid=False, rangemode="tozero")
        fig.update_yaxes(rangemode="tozero", secondary_y=False)
        ui.plot(fig, "ops_daily")
with d2c:
    with ui.card("ops-clock", "시간대별 Agent 작업 통계", "시간대별 자동 작업 (KST, 전체 기간 합)", "Clock"):
        hw = o.get("hourweek") or [[0] * 24 for _ in range(7)]
        hours = [sum(hw[w][h] for w in range(7)) for h in range(24)]
        mx = max(hours) or 1
        fig = go.Figure(go.Barpolar(r=hours, theta=[h * 15 for h in range(24)], width=[13] * 24,
                                    marker=dict(color=hours, colorscale=[[0, "#0e3a4f"], [1, "#67e8f9"]], line=dict(color="#0b1222", width=1)),
                                    customdata=[f"{h:02d}시" for h in range(24)], hovertemplate="%{customdata} · %{r:,}건<extra></extra>"))
        fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                     angularaxis=dict(rotation=90, direction="clockwise", tickmode="array", tickvals=[0, 90, 180, 270],
                                                      ticktext=["0시", "6시", "12시", "18시"], tickfont=dict(color=ui.MUTED, size=11),
                                                      gridcolor="rgba(148,163,184,.12)", linecolor="rgba(148,163,184,.2)"),
                                     radialaxis=dict(showticklabels=False, gridcolor="rgba(148,163,184,.08)", linecolor="rgba(0,0,0,0)")))
        ui.style(fig, 340, legend=False, margin=dict(l=40, r=40, t=24, b=24))
        ui.plot(fig, "ops_clock")
        night = sum(hours[h] for h in list(range(0, 7)) + [22, 23])
        ui.note(f"밤 10시~아침 7시 작업 {night:,}건 ({night / max(1, sum(hours)) * 100:.0f}%) — 사람이 쉬는 시간에도 돈다")

# ── 누적 성장 ──
g1, g2 = st.columns([1.3, 1], gap="medium")
with g1:
    with ui.card("ops-growth", "누적 수집 · 라벨링 곡선", "연구소 관련 문헌의 수집 → 초록 확보 → LLM 추출·도메인 배정 (날짜별 마지막 기록)", "Pipeline"):
        xs = [g["d"] for g in growth]
        fig = go.Figure()
        for key, name, col, fill in [("collected", "수집 (연구소 관련 문헌)", "#3987e5", "tozeroy"),
                                     ("abstract_ok", "초록 확보", "#22d3ee", "tozeroy"), ("assigned", "LLM 도메인 배정", "#d55181", "tozeroy")]:
            fig.add_trace(go.Scatter(x=xs, y=[g.get(key) for g in growth], name=name, mode="lines", fill=fill,
                                     line=dict(color=col, width=2.2), fillcolor=col + "22",
                                     hovertemplate=name + " %{x} · %{y:,}<extra></extra>"))
        ui.style(fig, 330)
        ui.plot(fig, "ops_growth")
with g2:
    with ui.card("ops-week", "주별 처리량", "한 주 동안 새로 모은 문헌 · 새로 LLM 라벨링한 문헌 (누적 기록의 주간 증가분)", "Weekly"):
        wk = {}
        prev = None
        for g in growth:
            if prev and g.get("collected") is not None and prev.get("collected") is not None:
                d = datetime.strptime(g["d"], "%Y-%m-%d")
                k = (d - timedelta(days=d.weekday())).strftime("%m/%d")
                a = wk.setdefault(k, [0, 0])
                a[0] += max(0, g["collected"] - prev["collected"])
                a[1] += max(0, (g.get("assigned") or 0) - (prev.get("assigned") or 0))
            prev = g
        ks = list(wk)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ks, y=[wk[k][0] for k in ks], name="새로 모음", marker=dict(color="#3987e5", cornerradius=3),
                             hovertemplate="%{x} 주 · 새로 모음 %{y:,}<extra></extra>"))
        fig.add_trace(go.Bar(x=ks, y=[wk[k][1] for k in ks], name="LLM 라벨링", marker=dict(color="#d55181", cornerradius=3),
                             hovertemplate="%{x} 주 · LLM 라벨링 %{y:,}<extra></extra>"))
        ui.style(fig, 330)
        fig.update_layout(barmode="group", bargap=0.25)
        fig.update_xaxes(type="category", title="주 시작일")
        ui.plot(fig, "ops_week")

# ── 월별 ──
with ui.card("ops-month", "월별 실적", "달마다 실행 횟수 · 가동 시간 · 새로 모은 문헌 · 새로 라벨링한 문헌", "Monthly"):
    mm = o.get("monthly") or []
    xs = [m["m"] for m in mm]
    fig = make_subplots(rows=1, cols=4, subplot_titles=("실행 횟수", "가동 시간 (시간)", "새로 모은 문헌", "새로 라벨링"), horizontal_spacing=0.06)
    for i, (key, col, f) in enumerate([("runs", "#22d3ee", 1), ("run_min", "#3b82f6", 1 / 60), ("collected_add", "#199e70", 1),
                                       ("assigned_add", "#d55181", 1)], start=1):
        ys = [(m.get(key) or 0) * f for m in mm]
        fig.add_trace(go.Bar(x=xs, y=ys, marker=dict(color=col, cornerradius=4), text=[f"{v:,.0f}" for v in ys], textposition="outside",
                             textfont=dict(size=10, color="#cbd5e1"), cliponaxis=False, hovertemplate="%{x} · %{y:,.0f}<extra></extra>"),
                      row=1, col=i)
    ui.style(fig, 260, legend=False, margin=dict(l=8, r=8, t=40, b=8))
    fig.update_annotations(font=dict(size=12, color=ui.MUTED))
    fig.update_xaxes(type="category", tickvals=xs, ticktext=[f"{int(m[5:])}월" for m in xs])
    fig.update_yaxes(showticklabels=False, showgrid=False)
    ui.plot(fig, "ops_month")

# ── 분야별 ──
f1, f2 = st.columns([1, 1], gap="medium")
with f1:
    with ui.card("ops-funnel", "분야별 처리 단계", "연구소마다 수집 → 초록 확보 → LLM 도메인 배정 (최근 기록)", "Funnel"):
        inow = o.get("inst_now") or {}
        mx = max([(inow.get(c) or {}).get("collected") or 0 for c in D.INST_ORDER] or [1]) or 1
        rows = []
        for c in D.INST_ORDER:
            x = inow.get(c) or {}
            col_, ab, asg = x.get("collected") or 0, x.get("abstract_ok") or 0, x.get("assigned") or 0
            rows.append(f'<div class="fn"><div class="fh"><b style="color:{ui.INST_COLORS[c]}">{D.INST_SHORT[c]}</b>'
                        f'<span>수집 {col_:,} · 초록 {ab:,} · 배정 <b>{asg:,}</b></span></div>'
                        f'<div class="fb"><i style="width:{col_ / mx * 100:.1f}%;background:{ui.INST_COLORS[c]}33"></i>'
                        f'<i style="width:{ab / mx * 100:.1f}%;background:{ui.INST_COLORS[c]}88"></i>'
                        f'<i style="width:{asg / mx * 100:.1f}%;background:{ui.INST_COLORS[c]}"></i></div></div>')
        ui.h('<div class="fns">' + "".join(rows) + "</div>")
        ui.note("연한 막대 = 수집, 중간 = 초록 확보, 진한 막대 = LLM이 대상·문제를 뽑고 도메인을 배정한 문헌")
with f2:
    with ui.card("ops-tasks", "수집 작업 목표 대비", "12개 핵심 저널 · 7개 연구소 대표 키워드 · K-water 소속 (2020~)", "Targets"):
        tasks = o.get("tasks") or []
        js = [t for t in tasks if t["code"].startswith("J")]
        others = [t for t in tasks if not t["code"].startswith("J")]
        rows = []
        for t in sorted(js, key=lambda t: -(t.get("target") or 0)) + others:
            p = (t.get("count") or 0) / max(1, t.get("target") or 1) * 100
            rows.append(f'<div class="tk"><span class="n">{ui.esc(str(t.get("name") or t["code"]))[:46]}</span>'
                        f'<span class="b"><i style="width:{min(100, p):.1f}%"></i></span>'
                        f'<span class="v">{t.get("count", 0):,}<em>/{t.get("target", 0):,}</em></span></div>')
        ui.h('<div class="tks">' + "".join(rows) + "</div>")

# ── 실시간 로그 + 워크플로 ──
l1, l2 = st.columns([1.6, 1], gap="medium")
with l1:
    with ui.card("ops-log", "실시간 실행 로그", "GitHub Actions 실행 기록과 에이전트 사건 기록 — 1분마다 다시 읽음", "Live log"):
        @st.fragment(run_every=60)
        def live_log():
            oo = D.ops()
            items = [("run", r) for r in (oo.get("recent") or [])[:45]] + [("ev", e) for e in (oo.get("events") or [])[:30]]
            items.sort(key=lambda x: -x[1]["ts"])
            lines = []
            for kind, r in items[:42]:
                t = datetime.fromtimestamp(r["ts"], KST).strftime("%m-%d %H:%M:%S")
                if kind == "run":
                    st_ = r.get("status")
                    cc = r.get("conclusion")
                    icon, cls = (("●", "run") if st_ != "completed" else ("✔", "ok") if cc == "success" else
                                 ("✖", "bad") if cc in ("failure", "timed_out") else ("–", "dim"))
                    lines.append(f'<div class="ln"><span class="t">{t}</span><span class="{cls}">{icon}</span>'
                                 f'<span class="wf">{ui.esc(r["wf"])}</span><span class="lb">{ui.esc(r.get("label", ""))}</span>'
                                 f'<span class="ev">{ui.esc(r.get("event") or "")}</span>'
                                 f'<span class="du">{"실행 중 " + dur(now - r["ts"]) if st_ != "completed" else dur(r.get("dur_s"))}</span></div>')
                else:
                    lines.append(f'<div class="ln"><span class="t">{t}</span><span class="evi">▸</span>'
                                 f'<span class="wf">{ui.esc(r["agent"])}</span><span class="msg">{ui.esc(r["msg"])}</span></div>')
            ui.h('<div class="term"><div class="bar"><i></i><i></i><i></i><span>co-scientist@actions: ~/agents — tail -f</span></div>'
                 '<div class="body">' + "".join(lines) + '<div class="ln"><span class="t">' +
                 datetime.now(KST).strftime("%m-%d %H:%M:%S") + '</span><span class="cur">█</span></div></div></div>')
        live_log()
with l2:
    with ui.card("ops-wf", "워크플로별 실행", "실행 횟수 · 쓴 시간 · 성공률", "Workflows"):
        ws = sorted(wfs.values(), key=lambda w: -w["minutes"])
        ui.ranked([{"label": w["label"], "value": w["minutes"] / 60,
                    "sub": f"{w['runs']:,}회 · 성공 {w['success'] / max(1, w['runs']) * 100:.0f}% · 최장 {dur(w['max_s'])}",
                    "color": "#22d3ee"} for w in ws[:9]], fmt="{:,.1f}시간")

# ── 실행 시간 분포 + 파이프라인 회차 ──
p1, p2 = st.columns([1, 1.3], gap="medium")
with p1:
    with ui.card("ops-dur", "한 번 돌 때 걸리는 시간", "워크플로별 실행 시간 분포 (로그 눈금) — 길게 버티는 작업이 많다", "Duration"):
        fig = go.Figure()
        for w in sorted(wfs.values(), key=lambda w: -w["runs"])[:8]:
            ds = [max(1, d) / 60 for d in (w.get("durs") or [])]
            if not ds:
                continue
            fig.add_trace(go.Box(x=ds, name=w["label"], orientation="h", boxpoints="outliers", marker=dict(size=3, color="#22d3ee"),
                                 line=dict(color="#67e8f9", width=1.2), fillcolor="rgba(34,211,238,.14)",
                                 hovertemplate="%{x:.1f}분<extra>" + w["label"] + "</extra>"))
        ui.style(fig, 340, legend=False)
        fig.update_xaxes(type="log", title="분", tickvals=[0.1, 0.5, 1, 5, 10, 30, 60], ticktext=["6초", "30초", "1분", "5분", "10분", "30분", "1시간"])
        ui.plot(fig, "ops_dur")
with p2:
    with ui.card("ops-pipe", "LLM 라벨링 파이프라인 회차", "회차마다 새로 모은 문헌 · 초록 보강 · LLM 추출 (점 크기 = 걸린 시간)", "Runs"):
        pl = [p for p in (o.get("pipeline") or []) if p.get("ts")]
        xs = [p["ts"].replace("T", " ")[:16] for p in pl]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=xs, y=[(p.get("forward") or 0) + (p.get("hist") or 0) for p in pl], name="새로 모음",
                             marker=dict(color="#3987e5", line_width=0), hovertemplate="%{x} · 새로 모음 %{y:,}<extra></extra>"))
        fig.add_trace(go.Bar(x=xs, y=[p.get("backfilled") or 0 for p in pl], name="초록 보강",
                             marker=dict(color="#22d3ee", line_width=0), hovertemplate="%{x} · 초록 보강 %{y:,}<extra></extra>"))
        ex = [p.get("extracted") or 0 for p in pl]
        fig.add_trace(go.Scatter(x=xs, y=ex, name="LLM 추출", mode="markers",
                                 marker=dict(size=[6 + 22 * math.sqrt((p.get("dur_s") or 0) / 3600) for p in pl], color="#d55181",
                                             line=dict(color="#0b1222", width=1), opacity=.85),
                                 customdata=[dur(p.get("dur_s")) for p in pl], hovertemplate="%{x} · LLM 추출 %{y:,} · %{customdata}<extra></extra>"))
        ui.style(fig, 340)
        fig.update_layout(barmode="group", bargap=0.1)
        fig.update_yaxes(type="log", title="편 (로그)", tickvals=[1, 10, 100, 1000, 10000], ticktext=["1", "10", "100", "1천", "1만"])
        ui.plot(fig, "ops_pipe")

# ── 쌓은 자산 + 장애 ──
a1, a2 = st.columns([1.6, 1], gap="medium")
with a1:
    with ui.card("ops-assets", "지금까지 다룬 자료", "수집·분석 에이전트가 손댄 자료의 규모 (모두 실제 건수)", "Scale"):
        items = [("수자원 핵심 12개 저널 논문 (상승 주제 분석)", T.get("oa_docs"), "편", "#9085e9"),
                 ("통합 물 지식 자산 (WCS 보고서·논문·특허)", T.get("wcs_assets"), "건", "#22d3ee"),
                 ("연구소 관련 문헌 수집 행", T.get("label_rows"), "행", "#3987e5"),
                 ("12개 핵심 저널 실수집", T.get("journal_papers"), "편", "#3b82f6"),
                 ("국내 학회지 논문 (KCI, 수자원·토목)", T.get("kci_docs"), "편", "#c98500"),
                 ("K-water 소속 국내 논문 (KCI)", T.get("kwater_kci"), "편", "#d95926"),
                 ("게재 저널 지표 (IF 역할)", T.get("journal_metrics"), "곳", "#d55181"),
                 ("기술 지도 OpenAlex 조회", T.get("tech_map_calls"), "회", "#199e70")]
        items = [i for i in items if i[1]]
        mx = max(math.log10(i[1] + 1) for i in items)
        ui.h('<div class="scl">' + "".join(
            f'<div class="sc"><span class="k">{ui.esc(k)}</span><span class="b"><i style="width:{math.log10(v + 1) / mx * 100:.1f}%;background:{c}"></i></span>'
            f'<span class="v">{v:,}<em>{u}</em></span></div>' for k, v, u, c in items) + "</div>")
        ui.note("막대는 로그 눈금 — 수십만 건과 수천 건을 한 줄에 놓으려고")
with a2:
    with ui.card("ops-fail", "장애 기록", "실패는 감추지 않고 남긴다 — 다음 회차가 이어 받음", "Incidents"):
        fs = o.get("failures") or {}
        bk = fs.get("by_kind") or {}
        KL = {"api_error": "API 오류 (재시도)", "empty_block": "초록 빈 응답", "workflow_failed": "워크플로 실패"}
        fig = go.Figure(go.Pie(labels=[KL.get(k, k) for k in bk], values=list(bk.values()), hole=.62, sort=False,
                               marker=dict(colors=["#f59e0b", "#fb7185", "#64748b", "#94a3b8"], line=dict(color="#0b1222", width=3)),
                               textinfo="none", hovertemplate="%{label} · %{value}건<extra></extra>"))
        fig.add_annotation(text=f"<b>{fs.get('total', 0)}</b><br><span style='font-size:11px;color:#94a3b8'>기록</span>", showarrow=False,
                           font=dict(size=20, color="#f8fafc"))
        ui.style(fig, 260, legend=True, margin=dict(l=0, r=0, t=10, b=0))
        fig.update_layout(legend=dict(orientation="v", x=1, y=.5, xanchor="left"))
        ui.plot(fig, "ops_fail")
        ok_rate = sum(w["success"] for w in wfs.values()) / max(1, sum(w["runs"] for w in wfs.values())) * 100
        ui.note(f"전체 실행 성공률 <b style='color:#e2e8f0'>{ok_rate:.1f}%</b> · "
                + " · ".join(f"{KL.get(k, k)} {v}건" for k, v in bk.items()) + " — 기록해 두고 다음 회차에서 다시 시도")

ui.note(f"자료: 물벗(newcave/water-tech-agent) 저장소의 커밋·GitHub Actions 실행 기록·파이프라인 로그 — 매시 53분 다시 셈 · "
        f"현황 기준 {datetime.fromtimestamp(o.get('updated', now), KST).strftime('%Y-%m-%d %H:%M')} KST"
        + (" · 스냅샷" if o.get("_src") == "snapshot" else ""))
