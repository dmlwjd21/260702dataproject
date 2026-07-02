import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


st.set_page_config(
    page_title="글로벌·한국 주식 데이터 분석 웹앱",
    page_icon="📈",
    layout="wide"
)

st.title("📈 글로벌·한국 주식 데이터 분석 웹앱")
st.caption("yfinance + Plotly + Streamlit Cloud")


# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("🔎 종목 설정")

market = st.sidebar.selectbox(
    "시장 선택",
    ["미국/글로벌", "한국 코스피", "한국 코스닥", "직접 입력"]
)

user_ticker = st.sidebar.text_input(
    "종목 코드 입력",
    value="AAPL",
    help="예: AAPL, MSFT, TSLA, 005930, 035720, 035420"
)

period = st.sidebar.selectbox(
    "조회 기간",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
    index=3
)

interval = st.sidebar.selectbox(
    "데이터 간격",
    ["1d", "1wk", "1mo"],
    index=0
)

ma_short = st.sidebar.number_input("단기 이동평균선", min_value=3, max_value=120, value=20)
ma_long = st.sidebar.number_input("장기 이동평균선", min_value=5, max_value=250, value=60)


def convert_ticker(ticker, market):
    ticker = ticker.strip().upper()

    if market == "한국 코스피":
        if ticker.isdigit():
            return ticker.zfill(6) + ".KS"
    elif market == "한국 코스닥":
        if ticker.isdigit():
            return ticker.zfill(6) + ".KQ"

    return ticker


ticker = convert_ticker(user_ticker, market)


# -----------------------------
# 데이터 불러오기
# -----------------------------
@st.cache_data(ttl=3600)
def load_data(ticker, period, interval):
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False
    )

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()

    return data


data = load_data(ticker, period, interval)


if data.empty:
    st.error("데이터를 불러오지 못했습니다. 종목 코드나 시장 선택을 확인해 주세요.")
    st.stop()


# -----------------------------
# 보조지표 계산
# -----------------------------
data["MA_short"] = data["Close"].rolling(ma_short).mean()
data["MA_long"] = data["Close"].rolling(ma_long).mean()
data["Daily_Return"] = data["Close"].pct_change() * 100

delta = data["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
data["RSI"] = 100 - (100 / (1 + rs))

ema12 = data["Close"].ewm(span=12, adjust=False).mean()
ema26 = data["Close"].ewm(span=26, adjust=False).mean()
data["MACD"] = ema12 - ema26
data["Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()


# -----------------------------
# 기본 정보
# -----------------------------
latest = data.iloc[-1]
previous = data.iloc[-2] if len(data) >= 2 else latest

price_change = latest["Close"] - previous["Close"]
price_change_pct = price_change / previous["Close"] * 100

col1, col2, col3, col4 = st.columns(4)

col1.metric("현재 종가", f"{latest['Close']:,.2f}")
col2.metric("전일 대비", f"{price_change:,.2f}", f"{price_change_pct:.2f}%")
col3.metric("거래량", f"{latest['Volume']:,.0f}")
col4.metric("최근 수익률 평균", f"{data['Daily_Return'].mean():.2f}%")


# -----------------------------
# 캔들 차트 + 이동평균 + 거래량
# -----------------------------
st.subheader(f"📊 {ticker} 가격 차트")

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.05,
    row_heights=[0.7, 0.3],
    subplot_titles=("가격", "거래량")
)

fig.add_trace(
    go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="캔들"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["MA_short"],
        mode="lines",
        name=f"{ma_short}일 이동평균"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["MA_long"],
        mode="lines",
        name=f"{ma_long}일 이동평균"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Bar(
        x=data.index,
        y=data["Volume"],
        name="거래량"
    ),
    row=2,
    col=1
)

fig.update_layout(
    height=750,
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)

st.plotly_chart(fig, width="stretch")


# -----------------------------
# 수익률 차트
# -----------------------------
st.subheader("📉 일별 수익률")

return_fig = go.Figure()

return_fig.add_trace(
    go.Bar(
        x=data.index,
        y=data["Daily_Return"],
        name="일별 수익률"
    )
)

return_fig.update_layout(
    height=400,
    yaxis_title="수익률(%)",
    hovermode="x unified"
)

st.plotly_chart(return_fig, width="stretch")


# -----------------------------
# RSI / MACD
# -----------------------------
st.subheader("🧭 기술적 지표")

tab1, tab2 = st.tabs(["RSI", "MACD"])

with tab1:
    rsi_fig = go.Figure()

    rsi_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["RSI"],
            mode="lines",
            name="RSI"
        )
    )

    rsi_fig.add_hline(y=70, line_dash="dash", annotation_text="과매수 기준 70")
    rsi_fig.add_hline(y=30, line_dash="dash", annotation_text="과매도 기준 30")

    rsi_fig.update_layout(
        height=400,
        yaxis_title="RSI",
        hovermode="x unified"
    )

    st.plotly_chart(rsi_fig, width="stretch")

with tab2:
    macd_fig = go.Figure()

    macd_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["MACD"],
            mode="lines",
            name="MACD"
        )
    )

    macd_fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Signal"],
            mode="lines",
            name="Signal"
        )
    )

    macd_fig.update_layout(
        height=400,
        yaxis_title="MACD",
        hovermode="x unified"
    )

    st.plotly_chart(macd_fig, width="stretch")


# -----------------------------
# 데이터 표
# -----------------------------
st.subheader("📋 원본 데이터")

show_columns = [
    "Open", "High", "Low", "Close", "Adj Close", "Volume",
    "MA_short", "MA_long", "Daily_Return", "RSI", "MACD", "Signal"
]

available_columns = [col for col in show_columns if col in data.columns]

st.dataframe(
    data[available_columns].sort_index(ascending=False),
    width="stretch"
)

csv = data.to_csv().encode("utf-8-sig")

st.download_button(
    label="CSV 다운로드",
    data=csv,
    file_name=f"{ticker}_stock_data.csv",
    mime="text/csv"
)


# -----------------------------
# 친절한 용어 설명
# -----------------------------
st.subheader("📘 주식 용어 쉽게 이해하기")

with st.expander("종가, 시가, 고가, 저가"):
    st.write("""
- **시가(Open)**: 장이 시작했을 때 처음 거래된 가격입니다.
- **고가(High)**: 해당 기간 동안 가장 높았던 가격입니다.
- **저가(Low)**: 해당 기간 동안 가장 낮았던 가격입니다.
- **종가(Close)**: 장이 끝났을 때 마지막으로 거래된 가격입니다.
""")

with st.expander("캔들 차트"):
    st.write("""
캔들 하나는 일정 기간의 가격 움직임을 보여줍니다.

- 가격이 올랐으면 보통 상승 캔들
- 가격이 내렸으면 보통 하락 캔들
- 몸통은 시가와 종가의 차이
- 꼬리는 고가와 저가의 범위

즉, 캔들은 하루 동안 주가가 어떻게 움직였는지 한눈에 보여주는 그림입니다.
""")

with st.expander("거래량"):
    st.write("""
**거래량**은 해당 기간 동안 주식이 얼마나 많이 사고팔렸는지를 뜻합니다.

거래량이 많다는 것은 그 종목에 관심이 많다는 뜻일 수 있습니다.
주가가 오르면서 거래량도 함께 늘면 상승 힘이 강하다고 해석하기도 합니다.
""")

with st.expander("이동평균선"):
    st.write("""
**이동평균선**은 일정 기간 동안의 평균 가격을 선으로 나타낸 것입니다.

예를 들어 20일 이동평균선은 최근 20일 종가의 평균입니다.

- 단기 이동평균선이 장기 이동평균선 위로 올라가면 상승 흐름으로 해석하기도 합니다.
- 단기 이동평균선이 장기 이동평균선 아래로 내려가면 하락 흐름으로 해석하기도 합니다.

다만 이동평균선은 과거 데이터를 평균낸 것이므로 항상 늦게 반응합니다.
""")

with st.expander("수익률"):
    st.write("""
**수익률**은 가격이 얼마나 올랐거나 내렸는지를 비율로 나타낸 것입니다.

예를 들어 10,000원이던 주식이 11,000원이 되면 수익률은 10%입니다.
반대로 10,000원이 9,000원이 되면 수익률은 -10%입니다.
""")

with st.expander("RSI"):
    st.write("""
**RSI**는 주가가 너무 많이 올랐는지, 너무 많이 내렸는지를 보는 지표입니다.

일반적으로 다음처럼 해석합니다.

- RSI 70 이상: 과매수 구간으로 볼 수 있음
- RSI 30 이하: 과매도 구간으로 볼 수 있음

하지만 RSI가 70 이상이라고 무조건 떨어지는 것은 아니고,
RSI가 30 이하라고 무조건 오르는 것도 아닙니다.
보조 참고 자료로 보는 것이 좋습니다.
""")

with st.expander("MACD"):
    st.write("""
**MACD**는 단기 흐름과 장기 흐름의 차이를 이용해 추세를 보는 지표입니다.

- MACD 선이 Signal 선 위로 올라가면 상승 신호로 해석하기도 합니다.
- MACD 선이 Signal 선 아래로 내려가면 하락 신호로 해석하기도 합니다.

하지만 MACD도 보조지표이므로 가격, 거래량, 시장 상황과 함께 봐야 합니다.
""")

st.info("""
⚠️ 이 앱은 투자 판단을 돕기 위한 데이터 분석 도구입니다.
매수·매도 추천이 아니며, 실제 투자는 본인의 판단과 책임으로 해야 합니다.
""")
