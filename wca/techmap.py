# -*- coding: utf-8 -*-
"""기술 지도 계산 — 물벗 tech_map/scores.json(세부 기술 41개 × 연도의 구성 지표 백분위)을 받아,
화면에서 고른 가중치로 X(논문)·Y(실용화)와 사분면을 다시 매긴다. 점수 설계의 주인은 물벗 agents/tech_map_score.py."""
import math

XK = ["V", "G", "Q", "J"]
YK = ["PV", "PG", "PR", "PC", "I"]
LABEL = {"V": "규모", "G": "성장", "Q": "피인용 질", "J": "저널 위상",
         "PV": "특허 규모", "PG": "특허 성장", "PR": "등록률", "PC": "기업 출원", "I": "산업계 공저"}
HELP = {"V": "최근 3년 논문 수", "G": "최근 5년 연 성장(물 분야 전체 대비)", "Q": "피인용 상위 10% 논문 비율(분야·연도 보정, 3년)",
        "J": "게재 저널의 2년 평균 피인용(IF와 같은 꼴, 2년)", "PV": "최근 3년 특허 출원", "PG": "최근 5년 출원 성장",
        "PR": "2~4년 전 출원의 등록률", "PC": "기업이 낸 출원 비율", "I": "기업 소속 저자가 참여한 논문 비율(3년)"}
QUAD = {"core": ("주력·코어", "#22d3ee", "논문↑ 실용화↑", "논문·실용화 모두 상위"),
        "gap": ("실용화 과제", "#f59e0b", "논문↑ 실용화↓", "논문 상위, 실용화 하위"),
        "applied": ("실용화 성숙", "#818cf8", "논문↓ 실용화↑", "논문 하위, 실용화 상위"),
        "review": ("검토 필요", "#64748b", "논문↓ 실용화↓", "논문·실용화 모두 하위"),
        "weak": ("위크시그널 후보", "#fb7185", "둘 다 하위, 성장 상위 30%", "모두 하위, 성장률 상위")}
QORDER = ["core", "gap", "applied", "weak", "review"]


def years(sc: dict) -> list:
    return sc.get("years") or []


def y_basis(sc: dict):
    return (sc.get("basis") or {}).get("y")


def weighted(c: dict, w: dict):
    got = [(c.get(k), wt) for k, wt in w.items() if wt and c.get(k) is not None]
    s = sum(wt for _, wt in got)
    return sum(v * wt for v, wt in got) / s if s else None


def quadrant(x, y, c: dict):
    if x is None or y is None:
        return None
    if x >= 50 and y >= 50:
        return "core"
    if x >= 50:
        return "gap"
    if y >= 50:
        return "applied"
    g = [v for v in (c.get("G"), c.get("PG")) if v is not None]
    return "weak" if g and max(g) >= 70 else "review"


def pct_rank(vals: dict) -> dict:
    """{id: 값} → {id: 0~100 백분위} (같은 값은 평균 순위) — 물벗 tech_map_score.pct_rank와 같은 규칙."""
    xs = sorted((v, k) for k, v in vals.items() if v is not None)
    n = len(xs)
    if n <= 1:
        return {k: 50.0 for _, k in xs}
    out, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and xs[j + 1][0] == xs[i][0]:
            j += 1
        for k in range(i, j + 1):
            out[xs[k][1]] = 100 * ((i + j) / 2) / (n - 1)
        i = j + 1
    return out


def rescore(sc: dict, wx: dict, wy: dict) -> dict:
    """{unit: {year: (x, y, quad)}} — 구성 지표 백분위를 가중 평균한 뒤, 그해 41개 사이에서 다시 백분위로 편다
    (평균은 가운데로 몰리므로 — 50선 = 41개의 중앙값)."""
    basis = y_basis(sc)
    wy_eff = wy if basis == "patents" else {"I": 1.0}
    us = sc.get("units") or {}
    out = {uid: {} for uid in us}
    for yr in years(sc):
        cs = {uid: (u.get("c") or {}).get(yr) or {} for uid, u in us.items()}
        xr = pct_rank({uid: weighted(c, wx) for uid, c in cs.items()})
        yr_ = pct_rank({uid: weighted(c, wy_eff) for uid, c in cs.items()}) if basis else {}
        for uid, c in cs.items():
            x, y = xr.get(uid), yr_.get(uid)
            out[uid][yr] = (x, y, quadrant(x, y, c))
    return out


def label_positions(xs, ys, names, char_w=1.25, h=2.6):
    """이름표 겹침을 줄이는 간단한 배치 — 위/아래/오른쪽/왼쪽 중 이미 놓인 이름표와 가장 덜 겹치는 쪽."""
    opts = [("top center", 0, h * .9), ("bottom center", 0, -h * .9), ("middle right", 1, 0), ("middle left", -1, 0)]
    placed, pos = [], [None] * len(xs)
    order = sorted(range(len(xs)), key=lambda i: -(ys[i] or 0))
    for i in order:
        w = max(4, len(names[i]) * char_w)
        best, best_ov = opts[0][0], 1e9
        for p, sx, dy in opts:
            cx = xs[i] + (sx * (w / 2 + 1.6))
            cy = ys[i] + dy
            box = (cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2)
            ov = sum(max(0, min(box[1], b[1]) - max(box[0], b[0])) * max(0, min(box[3], b[3]) - max(box[2], b[2])) for b in placed)
            if box[0] < -3 or box[1] > 103:
                ov += 50
            if ov < best_ov - 1e-9:
                best, best_ov, bb = p, ov, box
            if ov == 0:
                break
        placed.append(bb)
        pos[i] = best
    return pos


def size_of(n, nmax, lo=9, hi=34):
    if not n or not nmax:
        return lo
    return lo + (hi - lo) * math.sqrt(n / nmax)
