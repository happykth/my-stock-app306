import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------
# 기본 페이지 설정 (탭 제목, 아이콘, 레이아웃)
# ---------------------------------------------
st.set_page_config(
    page_title="주가 한눈에 보기",
    page_icon="📈",
    layout="centered"
)

# ---------------------------------------------
# 제목과 간단한 설명
# ---------------------------------------------
st.title("📈 주가 한눈에 보기")
st.write(
    "종목 코드를 입력하면 주가 흐름을 그래프로 보여드려요. 두 종목을 나란히 비교할 수도 있어요. "
    "예시) 삼성전자 **005930.KS**, 애플 **AAPL**"
)

# ---------------------------------------------
# 종목 코드 입력창 (최대 2개, 나란히 배치)
# ---------------------------------------------
input_col1, input_col2 = st.columns(2)

with input_col1:
    ticker_input_1 = st.text_input(
        "종목 코드 1",
        value="005930.KS",
        placeholder="예: 005930.KS"
    )

with input_col2:
    ticker_input_2 = st.text_input(
        "종목 코드 2 (선택)",
        value="",
        placeholder="예: AAPL"
    )

# 입력값 앞뒤 공백 제거 + 대문자로 통일
ticker_symbol_1 = ticker_input_1.strip().upper()
ticker_symbol_2 = ticker_input_2.strip().upper()

# ---------------------------------------------
# 조회 기간 선택 버튼 (1개월 / 6개월 / 1년 / 5년)
# ---------------------------------------------
# 선택된 기간을 기억하기 위한 세션 상태 (처음엔 1년으로 시작)
if "selected_period" not in st.session_state:
    st.session_state.selected_period = "1년"

# 기간 이름과 실제 일수를 매칭
period_days = {
    "1개월": 30,
    "6개월": 182,
    "1년": 365,
    "5년": 365 * 5
}

st.write("**조회 기간**")
period_cols = st.columns(4)

for col, period_label in zip(period_cols, period_days.keys()):
    with col:
        # 현재 선택된 기간이면 버튼 색을 다르게 표시(primary)
        is_selected = (st.session_state.selected_period == period_label)
        if st.button(
            period_label,
            use_container_width=True,
            type="primary" if is_selected else "secondary"
        ):
            st.session_state.selected_period = period_label

# 조회 버튼
search_clicked = st.button("조회하기", type="primary")


# ---------------------------------------------
# 주가 데이터를 불러와 지표를 계산하는 함수
# (종목 하나를 넣으면 데이터프레임과 지표 딕셔너리를 돌려줘요)
# ---------------------------------------------
def fetch_stock_data(ticker_symbol, start_date, end_date):
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(start=start_date, end=end_date)
    except Exception:
        return None, None, None

    if history is None or history.empty:
        return None, None, None

    # 회사 이름 가져오기 (없으면 종목 코드 그대로 사용)
    try:
        company_name = stock.info.get("longName", ticker_symbol)
    except Exception:
        company_name = ticker_symbol

    first_price = history["Close"].iloc[0]   # 기간 시작 시점 종가
    last_price = history["Close"].iloc[-1]    # 가장 최근 종가(현재가)

    change_amount = last_price - first_price
    change_percent = (change_amount / first_price) * 100

    metrics = {
        "현재가": last_price,
        "등락률": change_percent,
        "등락폭": change_amount,
        "최고가": history["Close"].max(),
        "최저가": history["Close"].min(),
        "평균가": history["Close"].mean(),
    }

    return history, metrics, company_name


# ---------------------------------------------
# 조회 버튼을 눌렀을 때만 데이터를 불러와요
# ---------------------------------------------
if search_clicked:

    if ticker_symbol_1 == "" and ticker_symbol_2 == "":
        # 종목 코드를 하나도 입력하지 않은 경우
        st.warning("종목 코드를 최소 1개 입력해 주세요.")
    else:
        # 선택된 기간(일수)에 맞춰 시작일 계산
        end_date = datetime.today()
        start_date = end_date - timedelta(days=period_days[st.session_state.selected_period])

        # 입력된 종목만 리스트에 담기 (빈 칸은 제외)
        tickers_to_fetch = [t for t in [ticker_symbol_1, ticker_symbol_2] if t != ""]

        results = {}  # 종목별로 (history, metrics, company_name) 저장

        with st.spinner("주가 데이터를 불러오는 중이에요..."):
            for ticker in tickers_to_fetch:
                history, metrics, company_name = fetch_stock_data(ticker, start_date, end_date)
                results[ticker] = (history, metrics, company_name)

        # 데이터를 하나도 못 불러온 경우
        valid_tickers = [t for t in tickers_to_fetch if results[t][0] is not None]

        if len(valid_tickers) == 0:
            st.error(
                "주가 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해 주세요. "
                "(예: 삼성전자 005930.KS, 애플 AAPL)"
            )
        else:
            # 못 찾은 종목이 있다면 안내만 하고 나머지는 계속 진행
            invalid_tickers = [t for t in tickers_to_fetch if t not in valid_tickers]
            for t in invalid_tickers:
                st.warning(f"'{t}' 종목 데이터를 찾을 수 없어 제외했어요.")

            # -------------------------------------------
            # 종목별 이름 및 현재가 · 등락률 지표 카드
            # -------------------------------------------
            metric_cols = st.columns(len(valid_tickers))

            for col, ticker in zip(metric_cols, valid_tickers):
                _, metrics, company_name = results[ticker]
                with col:
                    st.subheader(f"🏢 {company_name}")
                    st.metric(
                        label="현재가",
                        value=f"{metrics['현재가']:,.2f}"
                    )
                    st.metric(
                        label="등락률",
                        value=f"{metrics['등락률']:,.2f}%",
                        delta=f"{metrics['등락폭']:,.2f}"
                    )

            # -------------------------------------------
            # Plotly 꺾은선 그래프로 주가 흐름 비교
            # -------------------------------------------
            fig = go.Figure()

            # 따뜻한 톤의 색상 2가지 (첫 번째, 두 번째 종목)
            line_colors = ["#FFB703", "#E07A5F"]

            for i, ticker in enumerate(valid_tickers):
                history, _, company_name = results[ticker]
                fig.add_trace(
                    go.Scatter(
                        x=history.index,
                        y=history["Close"],
                        mode="lines",
                        name=f"{company_name} ({ticker})",
                        line=dict(color=line_colors[i % len(line_colors)], width=2.5)
                    )
                )

            fig.update_layout(
                title=f"주가 흐름 ({st.session_state.selected_period})",
                xaxis_title="날짜",
                yaxis_title="종가",
                template="plotly_white",
                hovermode="x unified",
                plot_bgcolor="#FFF8E7",   # 크림톤 배경
                paper_bgcolor="#FFF8E7",
                font=dict(size=14),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            st.plotly_chart(fig, use_container_width=True)

            # -------------------------------------------
            # 그래프 아래: 최고가 · 최저가 · 평균가 카드
            # -------------------------------------------
            st.write("**기간 내 가격 요약**")
            summary_cols = st.columns(len(valid_tickers))

            for col, ticker in zip(summary_cols, valid_tickers):
                _, metrics, company_name = results[ticker]
                with col:
                    st.markdown(f"**{company_name} ({ticker})**")
                    st.metric(label="최고가", value=f"{metrics['최고가']:,.2f}")
                    st.metric(label="최저가", value=f"{metrics['최저가']:,.2f}")
                    st.metric(label="평균가", value=f"{metrics['평균가']:,.2f}")

            # 원본 데이터 표로 확인하고 싶은 사람을 위한 접기 메뉴
            with st.expander("원본 데이터 표 보기"):
                for ticker in valid_tickers:
                    history, _, company_name = results[ticker]
                    st.write(f"**{company_name} ({ticker})**")
                    st.dataframe(history[["Open", "High", "Low", "Close", "Volume"]])

else:
    # 버튼을 아직 누르지 않았을 때 안내 문구
    st.info("종목 코드와 조회 기간을 선택하고 '조회하기' 버튼을 눌러주세요.")
