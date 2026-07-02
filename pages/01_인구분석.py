"""
📊 대한민국 인구 데이터 분석 대시보드
행정안전부 주민등록 연령별 인구현황(0세) 데이터를 활용한
청소년 대상 인구·출생 통계 탐구 대시보드

만든 목적: 정보/데이터분석/인공지능 수업에서 학생들이
실제 공공데이터를 가지고 '데이터로 세상 읽기'를 경험하도록 설계했습니다.
"""

import re
import glob
import io
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────
# 0. 기본 설정
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="👶 대한민국 인구·출생 데이터 대시보드",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

COLOR_MAIN = "#4C6EF5"
COLOR_SUB = "#FF8787"
COLOR_ACCENT = "#20C997"
PALETTE = px.colors.qualitative.Set2

CUSTOM_CSS = """
<style>
    .main > div {padding-top: 1.2rem;}
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
        border: 1px solid #e6e9f5;
        border-radius: 14px;
        padding: 14px 16px 8px 16px;
    }
    div[data-testid="stMetricLabel"] {font-weight: 600; color:#4C6EF5;}
    .insight-box {
        background: #F1F3FF;
        border-left: 6px solid #4C6EF5;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .fact-box {
        background: #FFF4E6;
        border-left: 6px solid #FF922B;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
    .quiz-box {
        background: #E6FCF5;
        border-left: 6px solid #20C997;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# 1. 데이터 로딩 & 전처리
# ──────────────────────────────────────────────────────────────────────────

REGION_ORDER = [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
    "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도",
    "충청북도", "충청남도", "전북특별자치도", "전라남도", "경상북도",
    "경상남도", "제주특별자치도",
]

REGION_SHORT = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남",
    "전북특별자치도": "전북", "전라남도": "전남", "경상북도": "경북",
    "경상남도": "경남", "제주특별자치도": "제주",
}


def _read_bytes_any_encoding(raw: bytes) -> pd.DataFrame:
    """CP949/EUC-KR로 저장된 KOSIS/행안부 CSV를 안전하게 읽어옵니다."""
    for enc in ("cp949", "euc-kr", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError("파일 인코딩을 인식할 수 없습니다. (cp949/euc-kr/utf-8 모두 실패)")


def _clean_region(name: str) -> str:
    return re.sub(r"\s*\(\d+\)\s*$", "", str(name)).strip()


def _to_number(x):
    if pd.isna(x):
        return np.nan
    return float(str(x).replace(",", "").strip())


@st.cache_data(show_spinner=False)
def parse_one_file(raw: bytes) -> pd.DataFrame:
    """
    행정안전부 '연령별 인구현황(0세)' 월간 CSV 1개를 tidy(long) 형태로 변환합니다.
    반환 컬럼: 행정구역, 년월, 성별, 총인구수, 0세인구수
    """
    df = _read_bytes_any_encoding(raw)
    df.columns = [c.strip() for c in df.columns]

    # 컬럼명에서 'YYYY년MM월' 패턴과 성별(계/남/여) 자동 추출
    month_pattern = re.compile(r"(\d{4})년(\d{2})월_(계|남|여)_(총인구수|연령구간인구수|0세)")
    long_rows = []

    region_col = df.columns[0]

    for _, row in df.iterrows():
        region = _clean_region(row[region_col])
        per_gender = {}
        for col in df.columns[1:]:
            m = month_pattern.search(col)
            if not m:
                continue
            yyyy, mm, gender, metric = m.groups()
            yyyymm = f"{yyyy}-{mm}"
            key = (yyyymm, gender)
            per_gender.setdefault(key, {})
            if metric == "총인구수":
                per_gender[key]["총인구수"] = _to_number(row[col])
            elif metric == "0세":
                per_gender[key]["0세인구수"] = _to_number(row[col])
            # '연령구간인구수'는 0세 단일 조회 시 0세와 동일값이므로 별도 사용 안 함

        for (yyyymm, gender), vals in per_gender.items():
            long_rows.append({
                "행정구역": region,
                "년월": yyyymm,
                "성별": gender,
                "총인구수": vals.get("총인구수", np.nan),
                "0세인구수": vals.get("0세인구수", np.nan),
            })

    tidy = pd.DataFrame(long_rows)
    tidy["약칭"] = tidy["행정구역"].map(lambda r: REGION_SHORT.get(r, r))
    return tidy


@st.cache_data(show_spinner=False)
def load_default_files() -> pd.DataFrame:
    files = sorted(glob.glob(str(DATA_DIR / "*.csv")))
    frames = []
    for f in files:
        with open(f, "rb") as fh:
            frames.append(parse_one_file(fh.read()))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["행정구역", "년월", "성별"])


def build_wide_metrics(tidy: pd.DataFrame) -> pd.DataFrame:
    """분석용 파생 지표를 계산합니다 (연도월 + 지역 단위)."""
    if tidy.empty:
        return tidy

    pivot_total = tidy.pivot_table(index=["행정구역", "약칭", "년월"], columns="성별",
                                    values="총인구수", aggfunc="first")
    pivot_age0 = tidy.pivot_table(index=["행정구역", "약칭", "년월"], columns="성별",
                                   values="0세인구수", aggfunc="first")

    out = pd.DataFrame(index=pivot_total.index)
    out["총인구_계"] = pivot_total.get("계")
    out["총인구_남"] = pivot_total.get("남")
    out["총인구_여"] = pivot_total.get("여")
    out["0세인구_계"] = pivot_age0.get("계")
    out["0세인구_남"] = pivot_age0.get("남")
    out["0세인구_여"] = pivot_age0.get("여")
    out = out.reset_index()

    out["0세비율(%)"] = (out["0세인구_계"] / out["총인구_계"] * 100).round(3)
    out["인구천명당0세"] = (out["0세인구_계"] / out["총인구_계"] * 1000).round(2)
    out["출생성비"] = (out["0세인구_남"] / out["0세인구_여"] * 100).round(1)  # 여아100명당 남아수
    return out


# ──────────────────────────────────────────────────────────────────────────
# 2. 사이드바 - 데이터 업로드 & 필터
# ──────────────────────────────────────────────────────────────────────────

st.sidebar.title("👶 인구 데이터 대시보드")
st.sidebar.caption("행정안전부 「연령별 인구현황(0세)」 기반")

st.sidebar.markdown("### 📂 데이터 불러오기")
uploaded_files = st.sidebar.file_uploader(
    "월별 CSV를 추가로 업로드하면 여러 달을 비교할 수 있어요! "
    "(행안부 주민등록인구 > 연령별인구현황 > 0세 조회 다운로드)",
    type=["csv"], accept_multiple_files=True,
)

with st.spinner("데이터를 불러오는 중이에요... ⏳"):
    default_tidy = load_default_files()
    frames = [default_tidy] if not default_tidy.empty else []
    for uf in uploaded_files or []:
        try:
            frames.append(parse_one_file(uf.getvalue()))
        except Exception as e:
            st.sidebar.error(f"'{uf.name}' 파일을 읽지 못했어요: {e}")

    if frames:
        tidy_all = pd.concat(frames, ignore_index=True).drop_duplicates(
            subset=["행정구역", "년월", "성별"])
    else:
        tidy_all = pd.DataFrame()

if tidy_all.empty:
    st.error("⚠️ 사용할 수 있는 데이터가 없습니다. CSV 파일을 업로드해 주세요.")
    st.stop()

metrics = build_wide_metrics(tidy_all)
available_months = sorted(metrics["년월"].unique())

st.sidebar.markdown("### 🗓️ 조회 월 선택")
selected_month = st.sidebar.selectbox(
    "기준 월", available_months, index=len(available_months) - 1,
    help="여러 달의 데이터를 올리면 이 목록이 늘어납니다.",
)

region_list = [r for r in REGION_ORDER if r in metrics["행정구역"].unique()]
st.sidebar.markdown("### 🗺️ 지역 선택")
selected_regions = st.sidebar.multiselect(
    "비교할 지역 (비워두면 전체)", region_list, default=[],
)
regions_for_view = selected_regions if selected_regions else region_list

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Tip.** 여러 달치 CSV를 함께 올리면 '📈 시계열 추이' 탭에서 "
    "우리 동네 0세 인구가 실제로 늘고 있는지 확인할 수 있어요!"
)

nation_row = metrics[(metrics["행정구역"].str.contains("전국")) & (metrics["년월"] == selected_month)]
region_rows_all = metrics[(metrics["년월"] == selected_month) & (~metrics["행정구역"].str.contains("전국"))]
region_rows = region_rows_all[region_rows_all["행정구역"].isin(regions_for_view)]

# ──────────────────────────────────────────────────────────────────────────
# 3. 헤더
# ──────────────────────────────────────────────────────────────────────────

st.title("👶 대한민국 인구·출생 데이터 탐구 대시보드")
st.markdown(
    f"**기준 월: `{selected_month}`** · 출처: 행정안전부 주민등록 인구통계(연령별 인구현황) "
    "· 이 대시보드는 교육용으로 제작되었습니다 🎓"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 전국 개요", "🗺️ 지역별 비교", "👶 출생 인사이트",
    "📈 시계열 추이", "📚 탐구 활동지",
])

# ──────────────────────────────────────────────────────────────────────────
# TAB 1. 전국 개요
# ──────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"🏠 {selected_month} 전국 인구 스냅샷")

    if nation_row.empty:
        st.warning("전국 합계 행을 찾을 수 없어요. 원본 CSV의 첫 행이 '전국'인지 확인해주세요.")
    else:
        n = nation_row.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🇰🇷 총인구", f"{n['총인구_계']:,.0f} 명")
        c2.metric("👶 0세 인구", f"{n['0세인구_계']:,.0f} 명")
        c3.metric("📊 0세 비율", f"{n['0세비율(%)']:.3f} %",
                   help="전체 인구 중 0세(만 0살)가 차지하는 비율")
        c4.metric("⚖️ 출생성비", f"{n['출생성비']:.1f}",
                   help="여아 100명당 남아 수. 자연 성비는 보통 103~107 사이")

        st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
        st.markdown(
            f"📌 **읽는 법** : 인구 {int(n['총인구_계']):,}명 중 0세 아기는 "
            f"{int(n['0세인구_계']):,}명으로, 인구 1,000명당 약 "
            f"**{n['인구천명당0세']:.1f}명**이 0세인 셈이에요. "
            "이 비율이 높을수록 그 지역에 '아기 인구'가 상대적으로 많다는 뜻이겠죠? 🍼"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns([1.3, 1])
        with col_a:
            gdf = pd.DataFrame({
                "성별": ["남", "여"],
                "0세인구": [n["0세인구_남"], n["0세인구_여"]],
            })
            fig = px.pie(
                gdf, names="성별", values="0세인구", hole=0.55,
                color="성별", color_discrete_map={"남": COLOR_MAIN, "여": COLOR_SUB},
                title="👶 전국 0세 인구 성별 구성",
            )
            fig.update_traces(textinfo="label+percent", pull=[0.02, 0.02])
            fig.update_layout(template="plotly_white", height=380,
                               legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("#### 🧮 빠른 계산기")
            st.write("우리반 학생 수를 넣으면, 그 인원이 태어난 해엔 몇 명의 아기가 있었을지 비교해볼까요?")
            class_size = st.number_input("우리반 학생 수", min_value=1, max_value=100, value=25)
            ratio = class_size / n['0세비율(%)'] * 100 if n['0세비율(%)'] else 0
            st.success(
                f"우리반 {class_size}명과 같은 '0세 비율'을 가지려면, "
                f"이 지역엔 약 **{ratio:,.0f}명**이 살아야 해요."
            )

# ──────────────────────────────────────────────────────────────────────────
# TAB 2. 지역별 비교
# ──────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader(f"🗺️ {selected_month} 시·도별 비교")

    if region_rows.empty:
        st.info("왼쪽에서 지역을 선택하거나, 전체 지역을 확인해보세요.")
    else:
        sort_metric = st.radio(
            "정렬 기준", ["총인구_계", "0세인구_계", "0세비율(%)", "출생성비"],
            horizontal=True, index=2,
        )
        sorted_df = region_rows.sort_values(sort_metric, ascending=False)

        fig_bar = px.bar(
            sorted_df, x="약칭", y=sort_metric, color=sort_metric,
            color_continuous_scale="Blues" if "인구" not in sort_metric else "Sunset",
            text_auto=".2s" if sort_metric != "0세비율(%)" else ".3f",
            title=f"📊 시·도별 {sort_metric} 비교",
            hover_data={"행정구역": True, "약칭": False},
        )
        fig_bar.update_layout(template="plotly_white", height=460,
                               xaxis_title="", yaxis_title=sort_metric,
                               coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            fig_tree = px.treemap(
                region_rows, path=["약칭"], values="총인구_계",
                color="0세비율(%)", color_continuous_scale="RdYlGn",
                title="🧩 인구 규모(면적) × 0세 비율(색상) 트리맵",
            )
            fig_tree.update_layout(template="plotly_white", height=420)
            st.plotly_chart(fig_tree, use_container_width=True)
        with c2:
            fig_scatter = px.scatter(
                region_rows, x="총인구_계", y="0세비율(%)", size="0세인구_계",
                color="약칭", text="약칭", size_max=45,
                title="🔍 총인구 vs 0세 비율 (거품 크기=0세 인구)",
                color_discrete_sequence=PALETTE,
            )
            fig_scatter.update_traces(textposition="top center")
            fig_scatter.update_layout(template="plotly_white", height=420, showlegend=False)
            st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("📋 원본 데이터 표로 보기"):
            show_cols = ["행정구역", "총인구_계", "총인구_남", "총인구_여",
                         "0세인구_계", "0세인구_남", "0세인구_여",
                         "0세비율(%)", "인구천명당0세", "출생성비"]
            st.dataframe(
                sorted_df[show_cols].style.format({
                    "총인구_계": "{:,.0f}", "총인구_남": "{:,.0f}", "총인구_여": "{:,.0f}",
                    "0세인구_계": "{:,.0f}", "0세인구_남": "{:,.0f}", "0세인구_여": "{:,.0f}",
                    "0세비율(%)": "{:.3f}", "인구천명당0세": "{:.2f}", "출생성비": "{:.1f}",
                }),
                use_container_width=True, height=380,
            )

# ──────────────────────────────────────────────────────────────────────────
# TAB 3. 출생 인사이트
# ──────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("👶 출생 관련 인사이트")

    if region_rows_all.empty:
        st.info("데이터가 부족합니다.")
    else:
        top3 = region_rows_all.sort_values("0세비율(%)", ascending=False).head(3)
        bottom3 = region_rows_all.sort_values("0세비율(%)").head(3)
        nat_ratio = nation_row.iloc[0]["0세비율(%)"] if not nation_row.empty else np.nan

        st.markdown("<div class='insight-box'>", unsafe_allow_html=True)
        st.markdown(
            f"🏆 **0세 비율이 가장 높은 지역** : "
            + ", ".join(f"{r['약칭']}({r['0세비율(%)']:.3f}%)" for _, r in top3.iterrows())
            + f"  \n🔻 **가장 낮은 지역** : "
            + ", ".join(f"{r['약칭']}({r['0세비율(%)']:.3f}%)" for _, r in bottom3.iterrows())
            + f"  \n🇰🇷 **전국 평균** : {nat_ratio:.3f}%"
        )
        st.markdown(
            "이 비율은 '그 지역 인구 중 0살 비중'이라, 실제 출산율(합계출산율)과는 다른 지표예요. "
            "예를 들어 청년층이 많이 모이는 도시는 0세 비율이 높게 나올 수 있고, "
            "고령 인구가 많은 지역은 낮게 나오는 경향이 있어요. **'많이 태어난 것'과 '비중이 높은 것'은 다르답니다.** 🤔"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        fig_rank = px.bar(
            region_rows_all.sort_values("0세비율(%)"),
            x="0세비율(%)", y="약칭", orientation="h",
            color="0세비율(%)", color_continuous_scale="Tealgrn",
            title="📶 시·도별 0세 인구 비율 순위",
        )
        fig_rank.add_vline(x=nat_ratio, line_dash="dash", line_color=COLOR_SUB,
                            annotation_text="전국 평균", annotation_position="top")
        fig_rank.update_layout(template="plotly_white", height=520, coloraxis_showscale=False)
        st.plotly_chart(fig_rank, use_container_width=True)

        fig_sex = px.bar(
            region_rows_all.sort_values("출생성비", ascending=False),
            x="약칭", y="출생성비", color="출생성비",
            color_continuous_scale="RdBu_r", range_color=[95, 115],
            title="⚖️ 시·도별 0세 성비 (여아 100명당 남아 수)",
        )
        fig_sex.add_hline(y=105, line_dash="dot", line_color="gray",
                           annotation_text="자연성비 기준선(105 내외)")
        fig_sex.update_layout(template="plotly_white", height=420, coloraxis_showscale=False)
        st.plotly_chart(fig_sex, use_container_width=True)

        st.markdown("### 📰 요즘 정말 출산율이 반등하고 있을까? (통계청 공식 발표 기준)")
        st.markdown("<div class='fact-box'>", unsafe_allow_html=True)
        st.markdown(
            "- 대한민국 합계출산율은 2023년 **0.72명**으로 역대 최저를 찍은 뒤, "
            "2024년 **0.75명**(9년 만의 반등), 2025년(잠정) **0.80명**으로 **2년 연속 상승**했어요.\n"
            "- 2024년 하반기부터 약 1년 반 동안 매달 전년 대비 출생아 수가 늘어나는 추세가 이어졌어요.\n"
            "- 반등을 이끈 건 특히 **30대 후반 여성의 출산율 증가**와, 코로나19로 미뤄졌던 **혼인 건수 증가**예요.\n"
            "- 지역별로는 2025년 기준 전남·세종·충북의 합계출산율이 높았고, "
            "서울·충북·인천 등은 전년 대비 증가폭이 컸다고 해요.\n\n"
            "⚠️ 다만 이 대시보드에 업로드된 CSV는 **1개월(또는 업로드된 달)의 스냅샷**이라 "
            "'비율'만으로는 반등 여부를 직접 증명할 수 없어요. "
            "**여러 달의 데이터를 모아야 진짜 추세를 볼 수 있겠죠?** 👉 아래 '시계열 추이' 탭에서 도전해보세요!"
        )
        st.markdown("</div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# TAB 4. 시계열 추이
# ──────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("📈 월별 시계열 추이")

    if len(available_months) < 2:
        st.markdown("<div class='quiz-box'>", unsafe_allow_html=True)
        st.markdown(
            "현재는 **1개 월치 데이터**만 있어서 시간에 따른 변화를 볼 수 없어요. 📅\n\n"
            "**직접 해보기** : 행정안전부 주민등록 인구통계 사이트에서 다른 달의 "
            "'연령별 인구현황(0세)' CSV를 추가로 내려받아 왼쪽 사이드바에 업로드해보세요. "
            "2~3개월치만 모아도 우리 동네 0세 인구가 늘고 있는지 줄고 있는지 확인할 수 있어요!"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        ts_regions = st.multiselect(
            "추이를 볼 지역 선택 (전국 포함 가능)",
            ["전국"] + region_list,
            default=["전국"],
        )
        ts_df = metrics[metrics["행정구역"].apply(
            lambda r: (r in ts_regions) or ("전국" in ts_regions and "전국" in r)
        )].sort_values("년월")

        fig_ts = px.line(
            ts_df, x="년월", y="0세비율(%)", color="행정구역", markers=True,
            title="👶 월별 0세 인구 비율 추이", color_discrete_sequence=PALETTE,
        )
        fig_ts.update_layout(template="plotly_white", height=460)
        st.plotly_chart(fig_ts, use_container_width=True)

        fig_ts2 = px.line(
            ts_df, x="년월", y="0세인구_계", color="행정구역", markers=True,
            title="👶 월별 0세 인구 수 추이", color_discrete_sequence=PALETTE,
        )
        fig_ts2.update_layout(template="plotly_white", height=420)
        st.plotly_chart(fig_ts2, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────
# TAB 5. 탐구 활동지 (교육용)
# ──────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("📚 수업에서 바로 쓰는 탐구 질문")
    st.markdown("<div class='quiz-box'>", unsafe_allow_html=True)
    st.markdown(
        "**1단계 - 관찰** : 0세 비율이 가장 높은 지역과 가장 낮은 지역을 찾고, "
        "그 차이가 왜 생겼을지 2가지 가설을 세워보세요.\n\n"
        "**2단계 - 비판적 사고** : '0세 비율이 높다 = 그 지역에서 아기를 많이 낳는다'는 "
        "문장이 왜 완전히 정확하지 않은지 설명해보세요. (힌트: 인구 이동, 전입·전출)\n\n"
        "**3단계 - 데이터 확장** : 통계청 KOSIS에서 최근 5년치 시·도별 합계출산율 데이터를 찾아, "
        "이 대시보드의 0세 비율 순위와 비교해보세요. 순위가 비슷한가요, 다른가요?\n\n"
        "**4단계 - 인공지능 연계** : 이 데이터를 학습 데이터로 삼아 '다음 달 0세 인구를 예측하는 AI'를 "
        "만든다면 어떤 한계가 있을지 토의해보세요. (데이터 편향, 표본 수 등)\n\n"
        "**5단계 - 정책 제안** : 출산율 반등의 원인(혼인 증가, 30대 후반 출산 증가 등)을 참고해, "
        "우리 지역에 맞는 저출생 대응 정책 아이디어를 하나 제안해보세요."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### 🧪 미니 퀴즈")
    q = st.radio(
        "다음 중 '0세 인구 비율'이 높다고 해서 반드시 참이라고 할 수 없는 것은?",
        [
            "그 지역 인구 중 0살의 비중이 크다",
            "그 지역에서 최근 태어난 아기가 절대적으로 가장 많다",
            "인구 1,000명당 0세 아기 수를 계산할 수 있다",
        ],
        index=None,
    )
    if q:
        if q == "그 지역에서 최근 태어난 아기가 절대적으로 가장 많다":
            st.success("정답이에요! 비율이 높아도 전체 인구가 적으면 절대적인 아기 수는 적을 수 있어요 🎉")
        else:
            st.error("다시 생각해볼까요? '비율'과 '절대적인 수'의 차이를 떠올려보세요 🤔")

st.markdown("---")
st.caption(
    "🛠️ Made with Streamlit & Plotly · 데이터 출처: 행정안전부 주민등록 인구통계(KOSIS 연계) · "
    "교육 목적으로 제작된 대시보드입니다."
)
