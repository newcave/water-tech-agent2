# -*- coding: utf-8 -*-
"""기술 지도 — 세부 기술 41개를 '논문 점수(X) × 실용화 점수(Y)' 평면에 놓고, 해마다 어디로 움직였는지 본다.
점수는 물벗 agents/tech_map_score.py가 매긴 구성 지표 백분위(그해 41개 사이 0~100)를 이 화면의 가중치로 다시 합친 것."""
import time

import plotly.graph_objects as go
import streamlit as st

from wca import data as D
from wca import techmap as T
from wca import ui

sc = D.tech_scores()
ag = D.tech_agent()
units = sc.get("units") or {}
yrs = T.years(sc)
basis = T.y_basis(sc)
bx = (sc.get("basis") or {}).get("x") or []

DEF_X = {"V": 25, "G": 25, "Q": 25, "J": 25}
DEF_Y = {"PV": 20, "PG": 20, "PR": 20, "PC": 20, "I": 20}
wx = {k: st.session_state.get(f"tm_w_{k}", v) for k, v in DEF_X.items() if k in bx}
wy = {k: st.session_state.get(f"tm_w_{k}", v) for k, v in DEF_Y.items()}
S = T.rescore(sc, wx, wy)
sel = st.session_state.get("tm_year") or (yrs[-1] if yrs else None)
if sel not in yrs and yrs:
    sel = yrs[-1]
x_name = "논문 점수 X →  (" + " · ".join(T.LABEL[k] for k in T.XK if k in bx) + ")"
y_name = {"patents": "실용화 (특허 + 산업계 공저)", "industry": "실용화 — 임시: 산업계 공저 논문", None: "실용화 (연결 대기)"}[basis]

ui.page_header("Technology map · Papers × Practicality", "기술 지도 — 논문 × 실용화",
               "세부 기술 41개에 해마다 두 점수를 매깁니다. <b style='color:#e2e8f0'>논문 점수</b>는 규모·성장·피인용 질·저널 위상, "
               "<b style='color:#e2e8f0'>실용화 점수</b>는 특허 규모·성장·등록률·기업 출원과 산업계 공저입니다. 둘을 한 평면에 놓으면 "
               "지금 주력인 것, 연구는 앞서는데 현장이 아직인 것, 이미 현장으로 간 것, 다시 들여다볼 것이 갈립니다.",
               [f"기준 <b>{sel or '–'}</b>", f"세부 기술 <b>{len(units)}</b>", f"Y <b>{'특허' if basis == 'patents' else '임시' if basis else '대기'}</b>"])

# ── 자료 연결 상태 (정직하게) ──
cnt = ag.get("counts") or {}
total_q = 41 * (5 + 10)
left_q = cnt.get("남은 조회", total_q)
done = max(0, total_q - left_q) / total_q * 100 if total_q else 0
errs = ag.get("last_errors") or []
blocked = any("429" in str(e) for e in errs)
paper_src = (sc.get("basis") or {}).get("paper_source") or []
n_scored = (sc.get("basis") or {}).get("units_scored", len(units))
p_pill = ('<span class="pill ok">완료</span>' if left_q == 0 else
          '<span class="pill bad">사용량 한도 — 키 필요</span>' if blocked and done == 0 else f'<span class="pill run">진행 {done:.0f}%</span>')
j_n = cnt.get("저널 지표", 0)
pat_n = (sc.get("basis") or {}).get("patents_total")
y_pill = ('<span class="pill ok">특허 연결</span>' if basis == "patents" else
          '<span class="pill run">임시 Y 사용</span>' if basis == "industry" else '<span class="pill wait">연결 대기</span>')
ui.h(f"""<div class="tmstat">
<div class="s"><div class="h"><b>논문 축 · OpenAlex</b>{p_pill}</div><div class="pb"><i style="width:{max(done, 2):.0f}%"></i></div>
<p>2016~2025 · 세부 기술마다 연도별 논문 수·피인용 상위 10%·기업 공저·K-water 소속·게재 저널.
{'지금 화면은 이미 받아 둔 2022~2025 값으로 먼저 계산했습니다.' if 'papers' not in paper_src else
  f'41개 중 {n_scored}개 수집 — 나머지는 다음 실행에서 이어 받습니다.' if n_scored < len(units) else ''}</p></div>
<div class="s"><div class="h"><b>저널 위상 · IF 역할</b><span class="pill {'ok' if j_n else 'wait'}">{f'{j_n:,}곳' if j_n else '대기'}</span></div>
<div class="pb"><i style="width:{100 if j_n else 2}%"></i></div>
<p>JCR 대신 OpenAlex 2년 평균 피인용(IF와 같은 계산 꼴, 공개 CC0). 연도별 SJR을 받으면 그해 값으로 바꿉니다.</p></div>
<div class="s"><div class="h"><b>실용화 축 · WCS 특허</b>{y_pill}</div><div class="pb"><i style="width:{100 if basis == 'patents' else 50 if basis else 2}%"></i></div>
<p>{f'세부 기술에 연결된 특허 {pat_n:,}건 (출원·등록·출원인 유형 집계만)' if basis == 'patents' else
    '특허 CSV가 오기 전까지는 기업 소속 저자가 참여한 논문 비율로 임시 Y를 그립니다.' if basis == 'industry' else
    '특허 CSV(WCS)와 산업계 공저 수집이 오면 Y축이 켜집니다. 가짜 숫자는 넣지 않습니다.'}</p></div>
</div>""")

if not units or not yrs:
    with ui.card("tm-empty", "점수 준비 중", "첫 계산이 끝나면 이 자리에 지도가 그려집니다", "Pending"):
        ui.note("물벗 tech-map 워크플로가 6시간마다 자료를 받아 점수를 다시 매깁니다.")
    st.stop()

# ── 사분면 개수 타일 ──
cur = {uid: S[uid].get(sel, (None, None, None)) for uid in units}
qcount = {k: sum(1 for v in cur.values() if v[2] == k) for k in T.QORDER}
if basis:
    ui.kpis([{"label": T.QUAD[k][0], "value": f"{qcount[k]}", "unit": "개", "sub": T.QUAD[k][3], "color": T.QUAD[k][1]}
             for k in T.QORDER])

# ── 지도 ──
m1, m2 = st.columns([2.3, 1], gap="medium")
with m1:
    with ui.card("tm-map", f"기술 지도 · {sel}", "점 하나 = 세부 기술 · 크기 = 최근 3년 논문 수 · 색 = 연구소 · 가운데 선 = 41개 중간(50)",
                 "Quadrant map" if basis else "Paper axis"):
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.segmented_control("연도", yrs, default=sel, key="tm_year", label_visibility="collapsed", width="content")
            trail = st.toggle("지나온 길", value=False, key="tm_trail") if basis and len(yrs) > 1 else False
            labels = st.toggle("이름", value=True, key="tm_lab")
            has_kw = any((units[u]["r"].get(sel) or {}).get("kw") for u in units)
            kwon = st.toggle("K-water 논문", value=True, key="tm_kw") if basis and has_kw else False
        insts = st.pills("연구소", D.INST_ORDER, selection_mode="multi", default=D.INST_ORDER, key="tm_inst",
                         format_func=lambda c: D.INST_SHORT[c], label_visibility="collapsed")
        show = [uid for uid, u in units.items() if u["inst"] in (insts or [])]
        nmax = max(((units[u]["r"].get(sel) or {}).get("n3") or 0) for u in units) if units else 1
        fig = go.Figure()
        if basis:
            for (x0, x1, y0, y1, k, ax, ay, xa, ya) in [(50, 105, 50, 116, "core", 104, 115, "right", "top"),
                                                         (50, 105, -16, 50, "gap", 104, -15, "right", "bottom"),
                                                         (-5, 50, 50, 116, "applied", -4, 115, "left", "top"),
                                                         (-5, 50, -16, 50, "review", -4, -15, "left", "bottom")]:
                c = T.QUAD[k][1]
                rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
                fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1, line_width=0, layer="below",
                              fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},.055)")
                sub = T.QUAD[k][2] + (" · 분홍 테 = 위크시그널 후보" if k == "review" else "")
                fig.add_annotation(x=ax, y=ay, xanchor=xa, yanchor=ya, showarrow=False, align=xa,
                                   text=f"<b>{T.QUAD[k][0]}</b><br><span style='font-size:10.5px;color:#94a3b8'>{sub}</span>",
                                   font=dict(size=13, color=c))
            for v in (50,):
                fig.add_shape(type="line", x0=v, x1=v, y0=-16, y1=116, line=dict(color="rgba(226,232,240,.28)", width=1, dash="dot"))
                fig.add_shape(type="line", x0=-5, x1=105, y0=v, y1=v, line=dict(color="rgba(226,232,240,.28)", width=1, dash="dot"))
            if trail:
                upto = [y for y in yrs if y <= sel]
                for uid in show:
                    pts = [S[uid][y] for y in upto if S[uid][y][0] is not None and S[uid][y][1] is not None]
                    if len(pts) < 2:
                        continue
                    col = ui.INST_COLORS[units[uid]["inst"]]
                    fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines+markers", hoverinfo="skip",
                                             showlegend=False, line=dict(color=col, width=1.2, shape="spline"), opacity=.35,
                                             marker=dict(size=3, color=col)))
            weak_x, weak_y, weak_s = [], [], []
            for c in D.INST_ORDER:
                ids = [u for u in show if units[u]["inst"] == c and cur[u][0] is not None and cur[u][1] is not None]
                if not ids:
                    continue
                xs, ys = [cur[u][0] for u in ids], [cur[u][1] for u in ids]
                ss = [T.size_of((units[u]["r"].get(sel) or {}).get("n3"), nmax) for u in ids]
                cd = [[units[u]["name"], D.INST_SHORT[c], T.QUAD[cur[u][2]][0] if cur[u][2] else "–",
                       (units[u]["r"].get(sel) or {}).get("n3") or 0] for u in ids]
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name=D.INST_SHORT[c], customdata=cd,
                                         marker=dict(size=ss, color=ui.INST_COLORS[c], opacity=.9, line=dict(color="#0b1222", width=1.5)),
                                         hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>논문 %{x:.0f} · 실용화 %{y:.0f}"
                                                       "<br>%{customdata[2]} · 최근 3년 %{customdata[3]:,}편<extra></extra>"))
                for u, s in zip(ids, ss):
                    if cur[u][2] == "weak":
                        weak_x.append(cur[u][0]); weak_y.append(cur[u][1]); weak_s.append(s + 10)
            if weak_x:
                fig.add_trace(go.Scatter(x=weak_x, y=weak_y, mode="markers", name="위크시그널 후보", hoverinfo="skip",
                                         marker=dict(symbol="circle-open", size=weak_s, color=T.QUAD["weak"][1], line=dict(width=2))))
            if kwon:                                           # '우리 논문' 겹쳐 보기 — K-water 소속(계열 포함) 최근 3년 논문
                kid = [u for u in show if cur[u][0] is not None and cur[u][1] is not None and (units[u]["r"].get(sel) or {}).get("kw")]
                if kid:
                    kv = [(units[u]["r"].get(sel) or {}).get("kw") for u in kid]
                    fig.add_trace(go.Scatter(x=[cur[u][0] + 2.4 for u in kid], y=[cur[u][1] + 3.2 for u in kid], mode="markers",
                                             name="K-water 논문", customdata=[[units[u]["name"], v] for u, v in zip(kid, kv)],
                                             marker=dict(symbol="diamond", size=[6 + 10 * (v / max(kv)) ** .5 for v in kv], color="#fde047",
                                                         line=dict(color="#0b1222", width=1)),
                                             hovertemplate="<b>%{customdata[0]}</b><br>K-water 소속 논문 최근 3년 %{customdata[1]}편<extra></extra>"))
            if labels:
                lid = [u for u in show if cur[u][0] is not None and cur[u][1] is not None]
                nm = [units[u]["name"] for u in lid]
                pos = T.label_positions([cur[u][0] for u in lid], [cur[u][1] for u in lid], nm)
                fig.add_trace(go.Scatter(x=[cur[u][0] for u in lid], y=[cur[u][1] for u in lid], mode="text", text=nm,
                                         textposition=pos, textfont=dict(size=10.5, color="#cbd5e1"), hoverinfo="skip", showlegend=False))
            ui.style(fig, 680, legend=True, margin=dict(l=10, r=10, t=40, b=10))
            fig.update_xaxes(range=[-5, 105], title=x_name, showgrid=False, tickvals=[0, 25, 50, 75, 100])
            fig.update_yaxes(range=[-16, 116], title=f"{y_name} →", showgrid=False, tickvals=[0, 25, 50, 75, 100])
        else:                                                  # Y가 아직 없으면: 연구소별 줄에 논문 점수만
            rows = [c for c in D.INST_ORDER if c in (insts or [])]
            for c in rows:
                ids = [u for u in show if units[u]["inst"] == c and cur[u][0] is not None]
                if not ids:
                    continue
                fig.add_trace(go.Scatter(
                    x=[cur[u][0] for u in ids], y=[D.INST_SHORT[c]] * len(ids), mode="markers+text" if labels else "markers",
                    text=[units[u]["name"] for u in ids], textposition=T.label_positions([cur[u][0] for u in ids], [0] * len(ids),
                                                                                       [units[u]["name"] for u in ids]),
                    textfont=dict(size=10, color="#cbd5e1"), name=D.INST_SHORT[c],
                    marker=dict(size=[T.size_of((units[u]["r"].get(sel) or {}).get("n3"), nmax) for u in ids],
                                color=ui.INST_COLORS[c], opacity=.9, line=dict(color="#0b1222", width=1.5)),
                    customdata=[[units[u]["name"], (units[u]["r"].get(sel) or {}).get("n3") or 0] for u in ids],
                    hovertemplate="<b>%{customdata[0]}</b><br>논문 점수 %{x:.0f} · 최근 3년 %{customdata[1]:,}편<extra></extra>"))
            fig.add_vline(x=50, line=dict(color="rgba(226,232,240,.3)", width=1, dash="dot"))
            ui.style(fig, 560, legend=False, margin=dict(l=10, r=10, t=20, b=10))
            fig.update_xaxes(range=[-5, 105], title=x_name)
            fig.update_yaxes(categoryorder="array", categoryarray=[D.INST_SHORT[c] for c in rows][::-1], showgrid=True)
        ui.plot(fig, f"tm_map_{sel}")
        ui.note("점수는 그해 41개 세부 기술 사이의 백분위(0~100)라 '상대 위치'입니다. 50선이 41개의 가운데입니다. "
                + ("지나온 길 = 첫 해부터 고른 해까지 움직인 자취 (연구소 하나만 골라 켜면 읽기 쉽습니다)." if basis else "실용화 축이 연결되면 같은 자리에 사분면 지도가 그려집니다."))

with m2:
    with ui.card("tm-quad", "사분면별 세부 기술" if basis else "논문 점수 순위", f"{sel}년 · " + ("두 점수 합이 높은 순" if basis else "상위 14개"),
                 "Quadrants" if basis else "Ranking"):
        if basis:
            blocks = []
            for k in T.QORDER:
                ids = sorted([u for u in units if cur[u][2] == k], key=lambda u: -((cur[u][0] or 0) + (cur[u][1] or 0)))
                chips = "".join(f'<span class="u"><i style="background:{ui.INST_COLORS[units[u]["inst"]]}"></i>{ui.esc(units[u]["name"])}</span>'
                                for u in ids)
                blocks.append(f'<div class="q" style="--qc:{T.QUAD[k][1]}"><div class="qh"><span class="c">{len(ids)}</span>'
                              f'<b>{T.QUAD[k][0]}</b><span class="d">{T.QUAD[k][3]}</span></div>'
                              + (f'<div class="us">{chips}</div>' if ids else '<div class="none">해당 없음</div>') + "</div>")
            ui.h('<div class="ql">' + "".join(blocks) + "</div>")
        else:
            top = sorted([u for u in units if cur[u][0] is not None], key=lambda u: -cur[u][0])
            ui.ranked([{"label": units[u]["name"], "sub": D.INST_SHORT[units[u]["inst"]], "value": cur[u][0],
                        "color": ui.INST_COLORS[units[u]["inst"]]} for u in top[:14]], fmt="{:.0f}", max_val=100)
            ui.note("실용화 축이 연결되기 전이라 논문 점수 순위만 보입니다.")

# ── 연도별 흐름 ──
order = sorted(units, key=lambda u: (D.INST_ORDER.index(units[u]["inst"]), u))
with ui.card("tm-heat", "연도별 흐름", "줄 = 세부 기술(연구소 순) · 칸 = 그해 위치 — 색이 바뀌는 곳이 사분면을 옮긴 해", "Timeline"):
    modes = (["사분면"] if basis else []) + ["논문 X"] + (["실용화 Y"] if basis else [])
    hm = st.segmented_control("색", modes, default=modes[0], key="tm_heat", label_visibility="collapsed")
    ticks = [f"<span style='color:{ui.INST_COLORS[units[u]['inst']]}'>●</span> {units[u]['name']}" for u in order]
    if hm == "사분면":
        idx = {k: i for i, k in enumerate(T.QORDER)}
        z = [[idx.get(S[u][y][2]) if S[u][y][2] else None for y in yrs] for u in order]
        n = len(T.QORDER)
        cs = []
        for i, k in enumerate(T.QORDER):
            cs += [[i / n, T.QUAD[k][1]], [(i + 1) / n, T.QUAD[k][1]]]
        ui.h('<div class="qlg">' + "".join(f'<span><i style="background:{T.QUAD[k][1]}"></i>{T.QUAD[k][0]}</span>' for k in T.QORDER) + "</div>")
        heat = go.Heatmap(z=z, x=yrs, y=ticks, zmin=-.5, zmax=n - .5, colorscale=cs, showscale=False, xgap=2, ygap=2,
                          customdata=[[[f"{S[u][y][0]:.0f}" if S[u][y][0] is not None else "–",
                                        f"{S[u][y][1]:.0f}" if S[u][y][1] is not None else "–",
                                        T.QUAD[S[u][y][2]][0] if S[u][y][2] else "–"] for y in yrs] for u in order],
                          hovertemplate="%{y}<br>%{x} · %{customdata[2]}<br>논문 %{customdata[0]} · 실용화 %{customdata[1]}<extra></extra>")
    else:
        k = 0 if hm == "논문 X" else 1
        z = [[S[u][y][k] for y in yrs] for u in order]
        heat = go.Heatmap(z=z, x=yrs, y=ticks, zmin=0, zmax=100, xgap=2, ygap=2, texttemplate="%{z:.0f}",
                          textfont=dict(size=10, color="#0b1222"),
                          colorscale=[[0, "#0f2236"], [.5, "#1d6a8a"], [1, "#67e8f9"]] if k == 0 else [[0, "#241a0a"], [.5, "#8a5a12"], [1, "#fcd34d"]],
                          colorbar=dict(thickness=10, len=.5, tickfont=dict(color=ui.MUTED, size=10), outlinewidth=0),
                          hovertemplate="%{y}<br>%{x} · %{z:.0f}<extra></extra>")
    fig = go.Figure(heat)
    ui.style(fig, 26 + 19 * len(order), legend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(size=11))
    fig.update_xaxes(side="top", showgrid=False, type="category")
    ui.plot(fig, f"tm_heat_{hm}")

if basis and len(yrs) > 1:
    s1, s2 = st.columns([3, 2], gap="medium")
    a, b = yrs[0], sel
    with s1:
        with ui.card("tm-sankey", f"사분면 이동 · {a} → {b}", "왼쪽 = 처음 해 위치, 오른쪽 = 고른 해 위치 · 띠 굵기 = 세부 기술 수", "Flow"):
            qa = {u: S[u][a][2] for u in units}
            qb = {u: S[u][b][2] for u in units}
            ks = [k for k in T.QORDER]
            lab = [f"{T.QUAD[k][0]} ({sum(1 for u in units if qa[u] == k)})" for k in ks] + \
                  [f"{T.QUAD[k][0]} ({sum(1 for u in units if qb[u] == k)})" for k in ks]
            src, dst, val, col, cdl = [], [], [], [], []
            for i, ka in enumerate(ks):
                for j, kb in enumerate(ks):
                    us = [u for u in units if qa[u] == ka and qb[u] == kb]
                    if us:
                        src.append(i); dst.append(len(ks) + j); val.append(len(us))
                        c = T.QUAD[ka][1]
                        col.append(f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},.32)")
                        cdl.append(", ".join(units[u]["name"] for u in us[:6]) + (" …" if len(us) > 6 else ""))
            fig = go.Figure(go.Sankey(
                arrangement="snap", node=dict(label=lab, pad=14, thickness=14, color=[T.QUAD[k][1] for k in ks] * 2,
                                              line=dict(color="#0b1222", width=1)),
                link=dict(source=src, target=dst, value=val, color=col, customdata=cdl,
                          hovertemplate="%{source.label} → %{target.label}<br>%{value}개 · %{customdata}<extra></extra>"),
                textfont=dict(color="#e2e8f0", size=12, family=ui.FONT)))
            ui.style(fig, 380, legend=False, margin=dict(l=8, r=8, t=8, b=8))
            ui.plot(fig, f"tm_sankey_{a}_{b}")
    with s2:
        with ui.card("tm-move", "가장 크게 움직인 세부 기술", f"{a} → {b} · 평면 위 이동 거리", "Movers"):
            mv = []
            for u in units:
                p0, p1 = S[u][a], S[u][b]
                if None in (p0[0], p0[1], p1[0], p1[1]):
                    continue
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                arrow = ("↗" if dx >= 0 and dy >= 0 else "↘" if dx >= 0 else "↖" if dy >= 0 else "↙")
                mv.append({"label": f"{arrow} {units[u]['name']}", "value": (dx * dx + dy * dy) ** .5,
                           "sub": f"논문 {dx:+.0f} · 실용화 {dy:+.0f}", "color": ui.INST_COLORS[units[u]["inst"]]})
            ui.ranked(sorted(mv, key=lambda r: -r["value"])[:9], fmt="{:.0f}")
            ui.note("↗ 둘 다 올라감 · ↘ 논문만 · ↖ 실용화만 · ↙ 둘 다 내려감")

# ── 세부 기술 들여다보기 ──
with ui.card("tm-unit", "세부 기술 들여다보기", "점수를 이루는 지표와 해마다의 두 점수, 그 안의 세세부 주제", "Drill-down"):
    default_u = max(units, key=lambda u: (cur[u][0] or 0) + (cur[u][1] or 0))
    pick = st.selectbox("세부 기술", order, index=order.index(default_u), key="tm_unit", label_visibility="collapsed",
                        format_func=lambda u: f"{D.INST_SHORT[units[u]['inst']]} · {units[u]['name']}  ({units[u]['en']})")
    u = units[pick]
    c = (u.get("c") or {}).get(sel) or {}
    r = (u.get("r") or {}).get(sel) or {}
    k1, k2, k3 = st.columns([1.1, 1.3, 1.2], gap="medium")
    with k1:
        keys = [k for k in T.XK if k in c] + [k for k in T.YK if k in c]
        fig = go.Figure(go.Bar(y=[T.LABEL[k] for k in keys][::-1], x=[c[k] for k in keys][::-1], orientation="h",
                               marker=dict(color=[("#3b82f6" if k in T.XK else "#f59e0b") for k in keys][::-1], cornerradius=4),
                               customdata=[T.HELP[k] for k in keys][::-1],
                               hovertemplate="%{y} · 백분위 %{x:.0f}<br>%{customdata}<extra></extra>"))
        fig.add_vline(x=50, line=dict(color="rgba(226,232,240,.35)", width=1, dash="dot"))
        ui.style(fig, 300, legend=False, margin=dict(l=8, r=8, t=26, b=8))
        fig.update_xaxes(range=[0, 100], title=f"{sel}년 백분위 (파랑 = 논문, 주황 = 실용화)")
        ui.plot(fig, f"tm_comp_{pick}_{sel}")
    with k2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=yrs, y=[S[pick][y][0] for y in yrs], name="논문 X", mode="lines+markers",
                                 line=dict(color="#3b82f6", width=2.6, shape="spline"), marker=dict(size=7)))
        if basis:
            fig.add_trace(go.Scatter(x=yrs, y=[S[pick][y][1] for y in yrs], name="실용화 Y", mode="lines+markers",
                                     line=dict(color="#f59e0b", width=2.6, shape="spline"), marker=dict(size=7)))
        fig.add_hline(y=50, line=dict(color="rgba(226,232,240,.3)", width=1, dash="dot"))
        ui.style(fig, 300, margin=dict(l=8, r=8, t=34, b=8))
        fig.update_yaxes(range=[0, 100])
        fig.update_xaxes(type="category")
        ui.plot(fig, f"tm_line_{pick}")
    with k3:
        q = cur[pick][2]
        qc = T.QUAD[q][1] if q else "#64748b"
        badge = f'<span class="badge" style="color:{qc};border-color:{qc}66;background:{qc}14">{T.QUAD[q][0] if q else "실용화 축 대기"}</span>'

        def fv(v, unit="", nd=0, plus=False):
            if v is None:
                return "–"
            return (f"{v:+,.{nd}f}" if plus else f"{v:,.{nd}f}") + (f"<small>{unit}</small>" if unit else "")
        cells = [("논문 (최근 3년)", fv(r.get("n3"), "편")), ("연 성장 (물 분야 대비)", fv(r.get("g"), "%", 1, True)),
                 ("피인용 상위 10%", fv(r.get("q"), "%", 1)), ("게재 저널 IF 역할", fv(r.get("j"), "", 2)),
                 ("산업계 공저", fv(r.get("i"), "%", 1)), ("K-water 논문 (3년)", fv(r.get("kw"), "편"))]
        if basis == "patents":
            cells += [("특허 출원 (3년)", fv(r.get("pv"), "건")), ("등록률", fv(r.get("pr"), "%", 1)),
                      ("기업 출원", fv(r.get("pc"), "%", 1)), ("특허 연 성장", fv(r.get("pg"), "%", 1, True))]
        tps = "".join(f'<span>{ui.esc(t[1] or t[0])}<em>{t[2]:,}</em></span>' for t in (u.get("topics") or [])[:6])
        ui.h(f'<div style="display:flex;justify-content:space-between;align-items:center;margin:2px 0 8px">{badge}'
             f'<span class="note" style="margin:0">{sel}년 · {D.INST_SHORT[u["inst"]]}</span></div>'
             f'<div class="fx">' + "".join(f"<div><span>{a}</span><b>{v}</b></div>" for a, v in cells) + "</div>"
             + (f'<div class="note" style="margin-top:10px">세세부 주제 후보 (OpenAlex topic · 10년 편수)</div><div class="tps">{tps}</div>' if tps else
                '<div class="note" style="margin-top:10px">세세부 주제(OpenAlex topic)는 수집이 끝나면 여기에 나옵니다.</div>'))

# ── 점수 설계 (토론용) ──
with ui.card("tm-weights", "점수 설계 — 가중치를 바꿔 보기", "바꾸면 위 지도·흐름·목록이 모두 다시 계산됩니다 (이 화면에서만)", "Method"):
    w1, w2, w3 = st.columns([1, 1, 1.4], gap="large")
    with w1:
        ui.h('<div class="ch"><div class="t" style="color:#93c5fd">논문 점수 X</div></div>')
        for k in T.XK:
            st.slider(f"{T.LABEL[k]} — {T.HELP[k]}", 0, 50, DEF_X[k], 5, key=f"tm_w_{k}", disabled=k not in bx)
    with w2:
        ui.h('<div class="ch"><div class="t" style="color:#fcd34d">실용화 점수 Y</div></div>')
        for k in T.YK:
            st.slider(f"{T.LABEL[k]} — {T.HELP[k]}", 0, 50, DEF_Y[k], 5, key=f"tm_w_{k}", disabled=basis != "patents")
        if basis != "patents":
            ui.note("특허가 연결되기 전에는 산업계 공저 하나로 Y를 계산합니다.")
    with w3:
        ui.h("""<div class="disc">
<div><b>점수는 상대 위치입니다.</b> 지표마다 그해 41개 세부 기술 사이의 백분위(0~100)를 매기고 가중 평균한 뒤, 그 평균을 다시 41개 사이 백분위로 폅니다(평균은 가운데로 몰리므로). 단위가 다른 지표(편수·비율·IF)를 한 눈금에 올리려는 선택이고, 50선은 41개의 중앙값입니다.</div>
<div><b>작은 표본은 가운데로 당깁니다.</b> 피인용 상위 10%·산업계 공저·등록률·기업 출원 같은 비율은 편수가 적으면 그해 전체 비율 쪽으로 당겨서(경험적 베이즈, 논문 30편·특허 10건 몫) 몇 편짜리 기술이 1등이 되지 않게 합니다.</div>
<div><b>성장은 물 분야 전체 대비</b>입니다. 41개 합계의 성장을 빼서 OpenAlex 색인 자체가 늘어난 효과를 덜어 냅니다.</div>
<div><b>IF는 공개 지표로 대신합니다.</b> 게재 저널의 2년 평균 피인용(OpenAlex, CC0)을 편수로 가중 평균합니다. JCR은 유료 라이선스라 쓰지 않습니다. 지금 값은 '받은 날' 기준이고, 연도별 SJR을 받으면 그해 값으로 바꿉니다.</div>
<div><b>사분면은 50선 기준</b>이고, 둘 다 50 아래인 기술 중 성장 백분위가 70 이상이면 <span style="color:#fb7185">위크시그널 후보</span>로 따로 표시합니다. 나머지는 비인기이거나 공백이라 사람이 들여다볼 대상입니다.</div>
<div><b>루베인 군집은 여기서 쓰지 않습니다.</b> 세부 기술은 연구소 키워드로 고정했고, 군집은 '떠오르는 주제' 탐지용으로만 씁니다.</div>
</div>""")
    if st.button("기본 가중치로", key="tm_reset", icon=":material/restart_alt:"):
        for k in list(DEF_X) + list(DEF_Y):
            st.session_state.pop(f"tm_w_{k}", None)
        st.rerun()

upd = sc.get("updated")
ui.note(f"점수 계산 {time.strftime('%Y-%m-%d %H:%M', time.gmtime(upd + 9 * 3600)) + ' KST' if upd else '–'} · "
        "세부 기술 정의서 v0.1(연구소 키워드 기준, 연구소 검토 전) · 특허 원천은 비공개, 이 화면은 건수 집계만 씁니다.")
