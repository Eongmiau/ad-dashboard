import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

# ── 페이지 설정 ────────────────────────────────────────────
st.set_page_config(
    page_title="광고 소재 성과 대시보드",
    page_icon="📊",
    layout="wide",
)

# ── 스타일 ─────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 4px solid #dee2e6;
    }
    .metric-label { font-size: 0.8rem; color: #6c757d; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #212529; margin-top: 0.2rem; }
    .metric-sub   { font-size: 0.8rem; color: #6c757d; margin-top: 0.2rem; }

    .tag-확장  { background:#d1fae5; color:#065f46; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .tag-디벨롭{ background:#dbeafe; color:#1e40af; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .tag-유지  { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .tag-개선  { background:#ffedd5; color:#9a3412; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .tag-중단  { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .tag-미분류{ background:#f3f4f6; color:#6b7280; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }

    .creative-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
    }
    .creative-title { font-size: 1rem; font-weight: 700; color: #111827; margin-bottom: 0.5rem; }
    .analysis-box {
        background: #f9fafb;
        border-left: 3px solid #6366f1;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #374151;
        margin-top: 0.8rem;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ── 데이터 로드 ────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))

# ── UI 시작 ────────────────────────────────────────────────
st.markdown("## 📊 광고 소재 성과 대시보드")

df = load_data()

if df.empty:
    st.info("아직 데이터가 없습니다. 매주 워크플로우 실행 후 자동으로 업데이트됩니다.")
    st.stop()

# ── 주차 선택 ──────────────────────────────────────────────
weeks = sorted(df["주차"].dropna().unique(), reverse=True) if "주차" in df.columns and df["주차"].notna().any() else []

if not weeks:
    periods = sorted(df["보고기간"].dropna().unique(), reverse=True)
    selected = st.sidebar.selectbox("📅 보고기간 선택", periods)
    filtered = df[df["보고기간"] == selected]
    period_label = selected
else:
    selected_week = st.sidebar.selectbox("📅 주차 선택", weeks)
    filtered = df[df["주차"] == selected_week]
    period_label = filtered["보고기간"].dropna().iloc[0] if not filtered["보고기간"].dropna().empty else selected_week

st.sidebar.markdown("---")
st.sidebar.markdown(f"**보고기간**  \n{period_label}")
st.sidebar.markdown(f"**소재 수**  \n{len(filtered)}개")

if st.sidebar.button("🔄 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# ── 요약 지표 ──────────────────────────────────────────────
total_spend = filtered["지출금액"].sum()
avg_roas    = filtered["ROAS"].mean()
avg_cpm     = filtered["CPM"].mean()
total_buys  = filtered["구매수"].sum()
count_확장  = (filtered["소재평가"] == "확장").sum()

c1, c2, c3, c4, c5 = st.columns(5)
def metric_card(col, label, value, sub=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

metric_card(c1, "총 지출",   f"₩{total_spend:,.0f}" if pd.notna(total_spend) else "-")
metric_card(c2, "평균 ROAS", f"{avg_roas:.2f}" if pd.notna(avg_roas) else "-", "목표 2.0 이상")
metric_card(c3, "평균 CPM",  f"₩{avg_cpm:,.0f}" if pd.notna(avg_cpm) else "-")
metric_card(c4, "총 구매수", f"{int(total_buys)}건" if pd.notna(total_buys) else "-")
metric_card(c5, "확장 소재", f"{count_확장}개", f"전체 {len(filtered)}개 중")

st.markdown("<br>", unsafe_allow_html=True)

# ── 차트 ───────────────────────────────────────────────────
color_map = {"확장":"#10b981","디벨롭":"#3b82f6","유지":"#f59e0b","개선":"#f97316","중단":"#ef4444","미분류":"#9ca3af"}
chart_df = filtered.dropna(subset=["이름"]).copy()
chart_df["태그"] = chart_df["소재평가"].fillna("미분류")
chart_df["이름_짧게"] = chart_df["이름"].str[:20]

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("#### ROAS 비교")
    roas_df = chart_df.dropna(subset=["ROAS"]).sort_values("ROAS", ascending=True)
    if not roas_df.empty:
        fig = px.bar(
            roas_df, x="ROAS", y="이름_짧게", orientation="h",
            color="태그", color_discrete_map=color_map,
            text="ROAS", height=max(300, len(roas_df)*45),
        )
        fig.add_vline(x=2.0, line_dash="dash", line_color="#6b7280", annotation_text="목표 2.0")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(margin=dict(l=0,r=20,t=10,b=10), legend_title="소재평가",
                          xaxis_title="ROAS", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown("#### CPM 비교")
    cpm_df = chart_df.dropna(subset=["CPM"]).sort_values("CPM", ascending=True)
    if not cpm_df.empty:
        fig2 = px.bar(
            cpm_df, x="CPM", y="이름_짧게", orientation="h",
            color="태그", color_discrete_map=color_map,
            text="CPM", height=max(300, len(cpm_df)*45),
        )
        fig2.update_traces(texttemplate="₩%{text:,.0f}", textposition="outside")
        fig2.update_layout(margin=dict(l=0,r=20,t=10,b=10),
                           xaxis_title="CPM (원)", yaxis_title="", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# ── 소재평가 분포 ───────────────────────────────────────────
tag_order = ["확장", "디벨롭", "유지", "개선", "중단", "-"]
tag_counts = filtered["소재평가"].value_counts().reindex(tag_order).dropna()

if not tag_counts.empty:
    st.markdown("#### 소재평가 분포")
    tag_bg = {"확장":"#d1fae5","디벨롭":"#dbeafe","유지":"#fef9c3","개선":"#ffedd5","중단":"#fee2e2","-":"#f3f4f6"}
    tag_tc = {"확장":"#065f46","디벨롭":"#1e40af","유지":"#854d0e","개선":"#9a3412","중단":"#991b1b","-":"#6b7280"}
    cols = st.columns(len(tag_counts))
    for i, (tag, cnt) in enumerate(tag_counts.items()):
        cols[i].markdown(f"""
        <div style="background:{tag_bg.get(tag,'#f3f4f6')};border-radius:10px;padding:1rem;text-align:center;">
            <div style="font-size:1.5rem;font-weight:800;color:{tag_tc.get(tag,'#374151')}">{int(cnt)}</div>
            <div style="font-size:0.8rem;font-weight:600;color:{tag_tc.get(tag,'#374151')}">{tag}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 소재별 카드 ─────────────────────────────────────────────
st.markdown("#### 소재별 상세")

tag_order_show = ["확장", "디벨롭", "유지", "개선", "중단", None, "-"]
sorted_df = filtered.copy()
sorted_df["_순서"] = sorted_df["소재평가"].map({t:i for i,t in enumerate(tag_order_show)}).fillna(99)
sorted_df = sorted_df.sort_values(["_순서", "ROAS"], ascending=[True, False])

for _, row in sorted_df.iterrows():
    tag = row.get("소재평가") or "미분류"
    tag_class = f"tag-{tag}" if tag in ["확장","디벨롭","유지","개선","중단"] else "tag-미분류"
    spend = f"₩{row['지출금액']:,.0f}" if pd.notna(row.get('지출금액')) else "-"
    roas  = f"{row['ROAS']:.2f}" if pd.notna(row.get('ROAS')) else "-"
    cpm   = f"₩{row['CPM']:,.0f}" if pd.notna(row.get('CPM')) else "-"
    buys  = f"{int(row['구매수'])}건" if pd.notna(row.get('구매수')) else "-"
    cpa   = f"₩{row['CPA']:,.0f}" if pd.notna(row.get('CPA')) else "-"
    analysis_html = f'<div class="analysis-box">🤖 {row["소재분석"]}</div>' if row.get("소재분석") else ""

    st.markdown(f"""
    <div class="creative-card">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div class="creative-title">{row.get('이름') or '(이름 없음)'}</div>
            <span class="{tag_class}">{tag}</span>
        </div>
        <div style="display:flex;gap:2rem;margin-top:0.6rem;flex-wrap:wrap;">
            <span style="font-size:0.85rem;color:#374151">💰 지출 <b>{spend}</b></span>
            <span style="font-size:0.85rem;color:#374151">📈 ROAS <b>{roas}</b></span>
            <span style="font-size:0.85rem;color:#374151">📡 CPM <b>{cpm}</b></span>
            <span style="font-size:0.85rem;color:#374151">🛒 구매 <b>{buys}</b></span>
            <span style="font-size:0.85rem;color:#374151">💵 CPA <b>{cpa}</b></span>
            <span style="font-size:0.85rem;color:#6b7280">{row.get('소재유형') or ''}</span>
        </div>
        {analysis_html}
    </div>""", unsafe_allow_html=True)
