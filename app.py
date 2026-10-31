# -*- coding: utf-8 -*-
"""Water Co-Scientist 쇼케이스 (water-tech-agent2) — v0.1 준비 화면.
숫자는 newcave/water-tech-agent 공개 집계(data_seed)를 그대로 읽는다. 본 화면은 다음 단계에서 전면 개편."""
import json
import urllib.request

import streamlit as st

SRC = "https://raw.githubusercontent.com/newcave/water-tech-agent/main/data_seed/"

st.set_page_config(page_title="Water Co-Scientist", page_icon="💧", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def seed(name):
    try:
        with urllib.request.urlopen(SRC + name, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return {}


assets = seed("wcs_assets.json")
total = sum(i.get("count", 0) for i in assets.get("items", []))
kci = seed("kci_kwater.json")
trends = seed("openalex_trends.json")
n_kw = (trends.get("history") or [{}])[-1].get("kwater")

st.markdown("""
<style>
.stApp {background: radial-gradient(1200px 600px at 10% -10%, #1b4f8a 0%, #0b1d33 55%, #070f1c 100%); color: #e8f1fb;}
.block-container {max-width: 1100px; padding-top: 4rem;}
.eyebrow {letter-spacing: .25em; font-size: .75rem; color: #7fb5e8; text-transform: uppercase;}
.hero h1 {font-size: clamp(2.4rem, 6vw, 4.2rem); line-height: 1.05; margin: .3rem 0 .8rem; color: #fff;}
.hero h1 span {background: linear-gradient(90deg, #5ee7f2, #7fb5e8); -webkit-background-clip: text; color: transparent;}
.hero p {color: #b9cde3; font-size: 1.1rem; max-width: 52ch;}
.kpis {display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 2.2rem;}
.kpi {background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12); border-radius: 18px; padding: 18px 20px;}
.kpi b {display: block; font-size: 2rem; color: #fff; font-variant-numeric: tabular-nums;}
.kpi span {color: #9fb8d3; font-size: .85rem;}
.soon {margin-top: 2.4rem; color: #7f97b2; font-size: .85rem;}
</style>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="hero">
  <div class="eyebrow">K-water Research Institute · AI Lab</div>
  <h1>물 연구의 흐름을 읽는<br><span>Water Co-Scientist</span></h1>
  <p>전 세계 물 연구 논문·국내 학회지·특허·K-water 연구보고서를 모아, 7개 연구소가 어디로 가야 할지 데이터로 보여 주는 R&amp;D 에이전트.</p>
</div>
<div class="kpis">
  <div class="kpi"><b>{total:,}</b><span>통합 물 지식 자산 (보고서·논문·특허)</span></div>
  <div class="kpi"><b>7</b><span>연구소별 트렌드 추적</span></div>
  <div class="kpi"><b>{kci.get('total', 0):,}</b><span>K-water 국내 학회지 논문 (KCI)</span></div>
  <div class="kpi"><b>{(n_kw or 0):,}</b><span>K-water 해외 논문 (OpenAlex, 2020~)</span></div>
</div>
<div class="soon">v0.1 · 쇼케이스 화면 준비 중 — 숫자는 물벗 R&amp;D 에이전트 공개 집계에서 실시간으로 읽습니다.</div>
""", unsafe_allow_html=True)
