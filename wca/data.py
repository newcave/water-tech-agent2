# -*- coding: utf-8 -*-
"""데이터 — 물벗(newcave/water-tech-agent) 공개 집계(data_seed)를 실시간으로 읽고, 못 읽으면 함께 넣어 둔 snapshot을 쓴다.
여기 있는 숫자는 모두 공개 집계(건수·비중·검정 결과)뿐 — KCI 원문·논문 목록은 없다."""
import json
import os
import time
import urllib.request
from pathlib import Path

import streamlit as st

RAW = "https://raw.githubusercontent.com/newcave/water-tech-agent/main/data_seed/"
SNAP = Path(__file__).resolve().parents[1] / "snapshot"

INST_ORDER = ["INST-01", "INST-02", "INST-03", "INST-04", "INST-05", "INST-06", "INST-07"]
INST_SHORT = {"INST-01": "경영", "INST-02": "수자원환경", "INST-03": "상하수도", "INST-04": "물인프라안전",
              "INST-05": "물에너지", "INST-06": "수자원위성", "INST-07": "AI"}
INST_EN = {"INST-01": "Management", "INST-02": "Water Resources & Env.", "INST-03": "Water Supply & Sewerage",
           "INST-04": "Infrastructure Safety", "INST-05": "Water Energy", "INST-06": "Satellite", "INST-07": "AI"}


@st.cache_data(ttl=1800, show_spinner=False)
def load(name: str) -> dict:
    """data_seed/<name> — GitHub 실시간, 실패하면 snapshot. (WCA_SEED_DIR가 있으면 그 폴더 먼저 — 로컬 시험용)"""
    local = os.environ.get("WCA_SEED_DIR")
    if local and (Path(local) / name).exists():
        d = json.loads((Path(local) / name).read_text(encoding="utf-8"))
        d["_src"] = "local"
        return d
    try:
        with urllib.request.urlopen(RAW + name, timeout=8) as r:
            d = json.loads(r.read().decode("utf-8"))
            d["_src"] = "live"
            return d
    except Exception:
        p = SNAP / name
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            d["_src"] = "snapshot"
            return d
        return {}


def agents() -> list:
    names = ["openalex_collector", "oa_rising", "alio_crawler", "alio_parser", "normalizer", "kipris_collector",
             "ft_trainer", "article_collector", "tech_map"]
    out = []
    for n in names:
        d = load(f"agents/{n}.json")
        if d:
            out.append({"id": n, **d})
    return out


# ── 해외 연구소 추이 (OpenAlex) ─────────────────────────────────────────

def trends() -> dict:
    return load("openalex_trends.json")


def years_full(tr: dict) -> list:
    y_now = time.gmtime().tm_year
    return [y for y in (tr.get("trend_years") or []) if int(y) < y_now]


def inst_series(ent: dict) -> dict:
    return ent.get("by_year_all") or ent.get("by_year") or {}


def inst_top10(ent: dict) -> dict:
    if ent.get("by_year_all"):
        return ent.get("by_year_all_top10") or {}
    return (ent.get("by_kw_top10") or {}).get(ent.get("keyword"), {})


def share(top: dict, tot: dict, years: list):
    n = sum((tot or {}).get(y, 0) for y in years)
    t = sum((top or {}).get(y, 0) for y in years)
    return t / n * 100 if n and top else None


def pct(a, b):
    return (b / a - 1) * 100 if a else None


def inst_table(tr: dict) -> list:
    """연구소별 요약 — 최근 끝난 해 편수, 첫해→마지막 해 성장, 해외 대비, 피인용 상위10% 비중, 연도 추이."""
    full = years_full(tr)
    base = (tr.get("baseline") or {}).get("by_year") or {}
    if len(full) < 2:
        return []
    a, b = full[0], full[-1]
    g_base = pct(base.get(a, 0), base.get(b, 0))
    rows = []
    for c in INST_ORDER:
        e = (tr.get("institutes") or {}).get(c)
        if not e:
            continue
        s = inst_series(e)
        g = pct(s.get(a, 0), s.get(b, 0))
        rows.append({"code": c, "name": INST_SHORT[c], "en": INST_EN[c], "last": s.get(b, 0), "first": s.get(a, 0),
                     "growth": g, "vs_base": g - g_base if g is not None and g_base is not None else None,
                     "top10": share(inst_top10(e), s, full), "series": [s.get(y, 0) for y in full],
                     "keywords": e.get("keywords") or [e.get("keyword")]})
    return rows


def keyword_table(tr: dict) -> list:
    full = years_full(tr)
    if len(full) < 2:
        return []
    a, b = full[0], full[-1]
    out = []
    for c in INST_ORDER:
        e = (tr.get("institutes") or {}).get(c) or {}
        top = e.get("by_kw_top10") or {}
        for k, v in (e.get("by_kw") or {}).items():
            out.append({"code": c, "inst": INST_SHORT[c], "kw": k, "first": v.get(a, 0), "last": v.get(b, 0),
                        "growth": pct(v.get(a, 0), v.get(b, 0)), "top10": share(top.get(k), v, full),
                        "n": sum(v.get(y, 0) for y in full), "series": [v.get(y, 0) for y in full]})
    return out


def baseline(tr: dict) -> dict:
    full = years_full(tr)
    base = tr.get("baseline") or {}
    by = base.get("by_year") or {}
    return {"growth": pct(by.get(full[0], 0), by.get(full[-1], 0)) if len(full) >= 2 else None,
            "top10": share(base.get("by_year_top10"), by, full), "series": [by.get(y, 0) for y in full]}


# ── 국내 (KCI) ─────────────────────────────────────────────────────────

def kci_kwater() -> dict:
    return load("kci_kwater.json")


def kci_inst() -> dict:
    return load("kci_inst.json")


def kci_rising() -> dict:
    return load("kci_rising.json")


# ── 떠오르는 주제 (수자원 12개 핵심 저널) ──────────────────────────────

def oa_rising() -> dict:
    return load("oa_rising/water_paper.json")


def assets() -> dict:
    return load("wcs_assets.json")


# ── 에이전트 수집 현황 (data 브랜치 live/ops/ops.json — 매시 갱신) ──────────

OPS_URL = "https://raw.githubusercontent.com/newcave/water-tech-agent/data/live/ops/ops.json"


@st.cache_data(ttl=120, show_spinner=False)
def ops() -> dict:
    """에이전트가 실제로 한 일의 건수 — 물벗 agents/ops_stats.py가 매시 씀. 못 읽으면 snapshot."""
    local = os.environ.get("WCA_SEED_DIR")
    if local and (Path(local) / "ops/ops.json").exists():
        d = json.loads((Path(local) / "ops/ops.json").read_text(encoding="utf-8"))
        d["_src"] = "local"
        return d
    try:
        with urllib.request.urlopen(f"{OPS_URL}?t={int(time.time() // 120)}", timeout=8) as r:
            d = json.loads(r.read().decode("utf-8"))
            d["_src"] = "live"
            return d
    except Exception:
        p = SNAP / "ops/ops.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            d["_src"] = "snapshot"
            return d
        return {}


# ── 기술 지도 (논문 × 실용화) ──────────────────────────────────────────

def tech_scores() -> dict:
    return load("tech_map/scores.json")


def tech_agent() -> dict:
    return load("agents/tech_map.json")


def updated_label() -> str:
    tr = trends()
    ts = tr.get("updated")
    src = tr.get("_src", "")
    if not ts:
        return "—"
    kst = time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts + 9 * 3600))
    return f"{kst} KST" + (" · 스냅샷" if src == "snapshot" else "")
