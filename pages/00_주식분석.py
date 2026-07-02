"""
📈 글로벌 · 국내 주식 데이터 분석 웹앱
- yfinance로 시세 데이터 수집
- plotly로 인터랙티브 차트 시각화
- Streamlit Cloud 배포용
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------
# Yahoo Finance 차단 우회용 세션
# ----------------------------------------------------------------------------
# yfinance의 기본 requests 방식은 Streamlit Cloud처럼 여러 사용자가
# IP를 공유하는 환경에서 Yahoo에게 쉽게 차단(429)당해요.
# curl_cffi로 실제 브라우저 TLS 지문을 흉내 내면 훨씬 안정적으로 응답을 받아요.
@st.cache_resource(show_spinner=False)
def get_yf_session():
    try:
        from curl_cffi import requests as cf_requests
        return cf_requests.Session(impersonate="chrome")
    except ImportError:
        return None  # curl_cffi 미설치 시 기본 세션으로 동작

# ----------------------------------------------------------------------------
# 기본 설정
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="주식 데이터 분석기",
    page_icon="📈",
    layout="wide",
)

# 자주 찾는 한국 종목 (yfinance는 KOSPI: .KS / KOSDAQ: .KQ 접미사 필요)
KOREAN_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "현대차": "005380.KS",
    "기아": "000270.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "셀트리온": "068270.KS",
    "POSCO홀딩스": "005490.KS",
    "삼성SDI": "006400.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "에코프로": "086520.KQ",
    "에코프로비엠": "247540.KQ",
    "카카오게임즈": "293490.KQ",
    "펄어비스": "263750.KQ",
}

# 자주 찾는 글로벌 종목
GLOBAL_STOCKS = {
    "애플 (Apple)": "AAPL",
    "마이크로소프트 (Microsoft)": "MSFT",
    "구글 (Alphabet)": "GOOGL",
    "아마존 (Amazon)": "AMZN",
    "엔비디아 (NVIDIA)": "NVDA",
    "테슬라 (Tesla)": "TSLA",
    "메타 (Meta)": "META",
    "넷플릭스 (Netflix)": "NFLX",
    "S&P500 지수": "^GSPC",
    "나스닥 지수": "^IXIC",
    "다우존스 지수": "^DJI",
}

TERM_EXPLANATIONS = {
    "캔들차트 (Candlestick Chart)": (
        "하루(또는 한 기간) 동안의 '시가(시작 가격)', '고가(가장 높았던 가격)', "
        "'저가(가장 낮았던 가격)', '종가(마감 가격)'를 하나의 막대(캔들) 모양으로 "
        "표현한 차트예요. 종가가 시가보다 높으면 보통 빨간색(또는 초록색), "
        "낮으면 반대 색으로 표시돼서 한눈에 상승/하락을 볼 수 있어요."
    ),
    "이동평균선 (Moving Average, MA)": (
        "최근 N일 동안의 종가를 평균 낸 값을 이어서 그린 선이에요. "
        "예를 들어 '20일 이동평균선'은 최근 20일간 종가 평균을 매일 계산해서 이은 선입니다. "
        "가격의 단기적인 흔들림(노이즈)을 부드럽게 걸러줘서 전체적인 추세(오르는 중인지, "
        "내리는 중인지)를 파악하는 데 도움을 줘요."
    ),
    "거래량 (Volume)": (
        "특정 기간 동안 실제로 사고 팔린 주식의 수량이에요. 거래량이 많다는 건 "
        "그 종목에 대한 시장의 관심이나 매매가 활발하다는 뜻이고, 가격이 크게 움직일 때 "
        "거래량도 함께 크게 늘어나면 그 움직임에 더 힘이 실려 있다고 해석하기도 해요."
    ),
    "시가총액 (Market Cap)": (
        "'현재 주가 × 발행 주식 수'로 계산되는, 그 회사 전체의 시장 가치예요. "
        "회사의 규모를 비교할 때 자주 사용하는 지표입니다."
    ),
    "PER (주가수익비율, Price Earning Ratio)": (
        "'주가 ÷ 주당순이익(EPS)'으로 계산해요. 지금 주가가 그 회사가 벌어들이는 "
        "이익에 비해 비싼 편인지 싼 편인지를 보여주는 대표적인 지표예요. "
        "숫자가 낮을수록 이익 대비 주가가 저렴하다고 볼 수 있지만, 업종마다 평균 수준이 달라서 "
        "같은 업종끼리 비교하는 게 더 의미 있어요."
    ),
    "52주 최고가/최저가": (
        "최근 52주(1년) 동안 그 주식이 기록한 가장 높은 가격과 가장 낮은 가격이에요. "
        "지금 주가가 그 범위 안에서 어디쯤 위치하는지 보면 현재 가격 수준을 가늠할 수 있어요."
    ),
    "등락률 (변동률)": (
        "전날(또는 기준 시점) 가격 대비 현재 가격이 몇 % 올랐는지, 내렸는지를 보여주는 수치예요. "
        "'+2.5%'면 2.5% 상승, '-1.3%'면 1.3% 하락했다는 뜻이에요."
    ),
    "골든크로스 / 데드크로스": (
        "골든크로스는 '단기 이동평균선'이 '장기 이동평균선'을 아래에서 위로 뚫고 올라가는 순간으로, "
        "흔히 상승 전환의 신호로 여겨져요. 반대로 데드크로스는 단기선이 장기선을 위에서 아래로 "
        "뚫고 내려가는 것으로, 하락 전환의 신호로 해석되곤 해요. (단, 항상 맞는 건 아니라서 "
        "참고 지표 중 하나로만 활용해야 해요!)"
    ),
}

# ----------------------------------------------------------------------------
# 데이터 로딩 함수
# ----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_data(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    df = yf.download(ticker, start=start, end=end, progress=False, session=get_yf_session())
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_info(ticker: str) -> dict:
    """
    yf.Ticker.info는 Yahoo Finance 스크래핑 방식이라 자주 실패하거나
    빈 값을 반환해요. 좀 더 안정적인 fast_info를 우선 사용하고,
    안 되면 info를 최대 2번까지 재시도합니다.
    그래도 실패하면 받아온 값들로 시가총액/PER을 직접 계산해봅니다.
    """
    result = {}
    t = yf.Ticker(ticker, session=get_yf_session())

    # 1) fast_info: 훨씬 안정적인 경량 API (시세 관련 핵심 정보)
    try:
        fi = t.fast_info
        result["currency"] = fi.get("currency")
        result["marketCap"] = fi.get("market_cap")
        result["fiftyTwoWeekHigh"] = fi.get("year_high")
        result["fiftyTwoWeekLow"] = fi.get("year_low")
        result["sharesOutstanding"] = fi.get("shares")
    except Exception:
        pass

    # 2) info: PER처럼 fast_info에 없는 값을 위해 보조로 시도 (최대 2회 재시도)
    info = {}
    for _ in range(2):
        try:
            info = t.info
            if info:
                for key in ("trailingPE", "currency", "marketCap",
                            "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
                            "sharesOutstanding", "trailingEps"):
                    if result.get(key) in (None, "N/A", 0) and info.get(key) not in (None, "N/A"):
                        result[key] = info.get(key)
                break
        except Exception:
            continue

    # 2-1) trailingPE/trailingEps가 없으면 Yahoo가 다른 이름으로 주는 값이 있는지 확인
    if result.get("trailingPE") in (None, "N/A") and isinstance(info.get("forwardPE"), (int, float)):
        result["trailingPE"] = info.get("forwardPE")
        result["perSource"] = "forwardPE(예상 실적 기준, 확정 실적 아님)"

    if result.get("trailingEps") in (None, "N/A"):
        alt_eps = info.get("epsTrailingTwelveMonths") or info.get("epsCurrentYear")
        if isinstance(alt_eps, (int, float)):
            result["trailingEps"] = alt_eps

    # 2-2) EPS 자체가 없으면 '순이익 ÷ 발행주식수'로 직접 계산 시도
    if result.get("trailingEps") in (None, "N/A"):
        net_income = info.get("netIncomeToCommon")
        shares = result.get("sharesOutstanding")
        if isinstance(net_income, (int, float)) and shares:
            result["trailingEps"] = net_income / shares
            result["epsSource"] = "netIncomeToCommon / sharesOutstanding"

    # 디버그용: Yahoo가 실제로 준 원본 전체 딕셔너리 보존
    result["_raw_info"] = info

    # 참고: 시가총액/PER이 여전히 없으면 이 함수 밖(메인 화면)에서
    # 이미 확보된 실제 종가(latest_close)를 이용해 직접 계산해요.
    # fast_info의 last_price는 자주 NULL이 나와서 계산 재료로 쓰지 않아요.

    return result


def infer_currency(ticker: str, info_currency) -> str:
    """info/fast_info에서 통화를 못 가져왔을 때 티커 접미사로 추정."""
    if info_currency:
        return info_currency
    if ticker.upper().endswith((".KS", ".KQ")):
        return "KRW"
    return "USD"


@st.cache_data(ttl=3600, show_spinner=False)
def load_52week_range(ticker: str):
    """info/fast_info가 실패할 경우를 대비해, 최근 1년치 데이터에서
    직접 52주 최고/최저가를 계산합니다."""
    try:
        hist = yf.download(
            ticker,
            start=datetime.today() - timedelta(days=365),
            end=datetime.today(),
            progress=False,
            session=get_yf_session(),
        )
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        if hist.empty:
            return None, None
        return float(hist["High"].max()), float(hist["Low"].min())
    except Exception:
        return None, None


def format_number(num):
    if num is None or num == "N/A":
        return "정보 없음"
    try:
        num = float(num)
    except (TypeError, ValueError):
        return "정보 없음"
    if abs(num) >= 1_0000_0000_0000:
        return f"{num / 1_0000_0000_0000:.2f}조"
    elif abs(num) >= 1_0000_0000:
        return f"{num / 1_0000_0000:.2f}억"
    return f"{num:,.0f}"


# ----------------------------------------------------------------------------
# 사이드바 - 사용자 입력
# ----------------------------------------------------------------------------
st.sidebar.title("🔍 종목 검색")

market = st.sidebar.radio("시장을 선택하세요", ["🇰🇷 한국 주식", "🌍 글로벌 주식", "✏️ 직접 입력"])

if market == "🇰🇷 한국 주식":
    name = st.sidebar.selectbox("종목 선택", list(KOREAN_STOCKS.keys()))
    ticker = KOREAN_STOCKS[name]
elif market == "🌍 글로벌 주식":
    name = st.sidebar.selectbox("종목 선택", list(GLOBAL_STOCKS.keys()))
    ticker = GLOBAL_STOCKS[name]
else:
    ticker = st.sidebar.text_input(
        "티커(종목코드)를 직접 입력하세요",
        value="AAPL",
        help="예: 애플=AAPL, 삼성전자=005930.KS, 카카오=035720.KS (한국 코스피는 .KS, 코스닥은 .KQ를 붙여요)",
    )
    name = ticker

st.sidebar.markdown("---")
st.sidebar.subheader("📅 조회 기간")

period_choice = st.sidebar.selectbox(
    "기간 선택",
    ["1개월", "3개월", "6개월", "1년", "3년", "5년", "직접 선택"],
    index=3,
)

end_date = datetime.today()
period_map = {
    "1개월": 30, "3개월": 90, "6개월": 180,
    "1년": 365, "3년": 365 * 3, "5년": 365 * 5,
}

if period_choice == "직접 선택":
    col_a, col_b = st.sidebar.columns(2)
    start_date = col_a.date_input("시작일", value=end_date - timedelta(days=365))
    end_date = col_b.date_input("종료일", value=end_date)
else:
    start_date = end_date - timedelta(days=period_map[period_choice])

st.sidebar.markdown("---")
st.sidebar.subheader("📊 차트 옵션")
show_ma = st.sidebar.multiselect(
    "이동평균선 표시 (일)",
    [5, 20, 60, 120],
    default=[20, 60],
)
chart_type = st.sidebar.radio("차트 종류", ["캔들차트", "라인차트"])

# ----------------------------------------------------------------------------
# 메인 화면
# ----------------------------------------------------------------------------
st.title("📈 글로벌 · 국내 주식 데이터 분석기")
st.caption("yfinance로 실시간 데이터를 불러오고, plotly로 인터랙티브하게 시각화합니다.")

with st.spinner(f"'{name}' 데이터를 불러오는 중입니다..."):
    df = load_stock_data(ticker, start_date, end_date)
    info = load_stock_info(ticker)

if df.empty:
    st.error("데이터를 불러오지 못했어요. 티커(종목코드)가 올바른지 확인해주세요. "
              "(한국 종목은 코스피 .KS, 코스닥 .KQ 접미사가 꼭 필요해요)")
    st.stop()

df = df.dropna(subset=["Close"])

# ----------------------------------------------------------------------------
# 상단 요약 지표
# ----------------------------------------------------------------------------
latest_close = float(df["Close"].iloc[-1])
prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else latest_close
change = latest_close - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0
currency = infer_currency(ticker, info.get("currency"))

# info/fast_info에서 52주 최고·최저가를 못 가져왔으면 실데이터로 직접 계산
week52_high = info.get("fiftyTwoWeekHigh")
week52_low = info.get("fiftyTwoWeekLow")
if week52_high in (None, "N/A") or week52_low in (None, "N/A"):
    computed_high, computed_low = load_52week_range(ticker)
    week52_high = week52_high if week52_high not in (None, "N/A") else computed_high
    week52_low = week52_low if week52_low not in (None, "N/A") else computed_low

# 시가총액이 없으면 '실제 종가 × 발행주식수'로 직접 계산
# (fast_info의 last_price는 자주 NULL이라, 이미 확보된 latest_close를 사용)
market_cap = info.get("marketCap")
market_cap_estimated = False
shares_outstanding = info.get("sharesOutstanding")
if market_cap in (None, "N/A") and shares_outstanding:
    market_cap = latest_close * shares_outstanding
    market_cap_estimated = True

# PER이 없으면 '실제 종가 ÷ 주당순이익(EPS)'으로 직접 계산
per_value = info.get("trailingPE")
per_estimated = False
trailing_eps = info.get("trailingEps")
if per_value in (None, "N/A") and trailing_eps:
    try:
        per_value = latest_close / trailing_eps
        per_estimated = True
    except ZeroDivisionError:
        pass

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    label=f"현재가 ({currency})",
    value=f"{latest_close:,.2f}",
    delta=f"{change:+,.2f} ({change_pct:+.2f}%)",
)
c2.metric("52주 최고가", format_number(week52_high))
c3.metric("52주 최저가", format_number(week52_low))

market_cap_label = "시가총액 (추정)" if market_cap_estimated else "시가총액"
c4.metric(market_cap_label, format_number(market_cap))

per_label = "PER (추정)" if per_estimated else "PER"
c5.metric(per_label, f"{per_value:.2f}" if isinstance(per_value, (int, float)) else "정보 없음")

if per_value in (None, "N/A") or market_cap in (None, "N/A"):
    st.caption(
        "ℹ️ 시가총액·PER·EPS 관련 필드를 Yahoo Finance가 이 종목에 대해 "
        "아예 제공하지 않는 경우 '정보 없음'이 정확한 표시예요. "
        "(특히 한국 거래소 종목은 Yahoo의 재무 데이터가 비어있는 경우가 종종 있어요)"
    )

with st.expander("🔧 디버그: 원본 데이터 확인"):
    st.write("정리해서 사용 중인 값:")
    st.json({k: v for k, v in info.items() if k != "_raw_info"})

    st.write("최종 계산/표시된 값:")
    st.json({
        "latest_close(실제 종가)": latest_close,
        "market_cap(최종)": market_cap,
        "market_cap_estimated": market_cap_estimated,
        "per(최종)": per_value,
        "per_estimated": per_estimated,
    })

    st.write("Yahoo가 이 종목에 대해 실제로 보낸 전체 원본 데이터 "
              "(다른 필드명으로 PER/EPS 관련 값이 있는지 여기서 직접 확인할 수 있어요):")
    st.json(info.get("_raw_info", {}))

st.markdown("---")

# ----------------------------------------------------------------------------
# 캔들/라인 + 거래량 차트
# ----------------------------------------------------------------------------
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    vertical_spacing=0.03, row_heights=[0.75, 0.25],
    subplot_titles=(f"{name} 가격 추이", "거래량"),
)

if chart_type == "캔들차트":
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color="#ef5350", decreasing_line_color="#1e88e5",
            name="가격",
        ),
        row=1, col=1,
    )
else:
    fig.add_trace(
        go.Scatter(x=df.index, y=df["Close"], mode="lines",
                    line=dict(color="#1e88e5", width=2), name="종가"),
        row=1, col=1,
    )

ma_colors = {5: "#ff9800", 20: "#8e24aa", 60: "#43a047", 120: "#546e7a"}
for ma in show_ma:
    df[f"MA{ma}"] = df["Close"].rolling(window=ma).mean()
    fig.add_trace(
        go.Scatter(x=df.index, y=df[f"MA{ma}"], mode="lines",
                    line=dict(color=ma_colors.get(ma, "#000"), width=1.3),
                    name=f"{ma}일 이동평균"),
        row=1, col=1,
    )

volume_colors = [
    "#ef5350" if df["Close"].iloc[i] >= df["Open"].iloc[i] else "#1e88e5"
    for i in range(len(df))
]
fig.add_trace(
    go.Bar(x=df.index, y=df["Volume"], marker_color=volume_colors, name="거래량"),
    row=2, col=1,
)

fig.update_layout(
    height=700,
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=60, b=10),
)
fig.update_yaxes(title_text="가격", row=1, col=1)
fig.update_yaxes(title_text="거래량", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------------------
# 데이터 테이블 & 다운로드
# ----------------------------------------------------------------------------
st.subheader("📋 원본 데이터")
show_df = df.copy()
show_df.index = show_df.index.strftime("%Y-%m-%d")
st.dataframe(show_df.sort_index(ascending=False), use_container_width=True)

csv = show_df.to_csv().encode("utf-8-sig")
st.download_button(
    "⬇️ CSV로 다운로드",
    data=csv,
    file_name=f"{ticker}_stock_data.csv",
    mime="text/csv",
)

# ----------------------------------------------------------------------------
# 주식 용어 설명
# ----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📚 주식 용어 쉽게 알아보기")
st.caption("차트를 보다가 낯선 용어가 나오면 아래에서 펼쳐서 확인해보세요!")

for term, explanation in TERM_EXPLANATIONS.items():
    with st.expander(term):
        st.write(explanation)

st.markdown("---")
st.caption(
    "⚠️ 이 앱은 교육 및 정보 제공 목적으로 제작되었으며, 투자 조언이 아닙니다. "
    "데이터는 Yahoo Finance(yfinance)에서 제공하며 실시간과 차이가 있을 수 있어요."
)
