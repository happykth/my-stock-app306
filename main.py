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
    "종목 코드를 입력하면 최근 1년간의 주가 흐름을 그래프로 보여드려요. "
    "예시) 삼성전자 **005930.KS**, 애플 **AAPL**"
)

# ---------------------------------------------
# 종목 코드 입력창
# ---------------------------------------------
ticker_input = st.text_input(
    "종목 코드를 입력해 주세요",
    value="005930.KS",
    placeholder="예: 005930.KS, AAPL"
)

# 입력값 앞뒤 공백 제거 + 대문자로 통일
ticker_symbol = ticker_input.strip().upper()

# 조회 버튼
search_clicked = st.button("조회하기", type="primary")

# ---------------------------------------------
# 조회 버튼을 눌렀을 때만 데이터를 불러와요
# ---------------------------------------------
if search_clicked:

    if ticker_symbol == "":
        # 종목 코드를 입력하지 않은 경우
        st.warning("종목 코드를 입력해 주세요.")
    else:
        # 로딩 중임을 알려주는 스피너
        with st.spinner("주가 데이터를 불러오는 중이에요..."):

            # 오늘 날짜와 1년 전 날짜 계산
            end_date = datetime.today()
            start_date = end_date - timedelta(days=365)

            try:
                # yfinance로 최근 1년치 일별 주가 데이터 가져오기
                stock = yf.Ticker(ticker_symbol)
                history = stock.history(start=start_date, end=end_date)
            except Exception:
                # 네트워크 오류 등 예외 상황 처리
                history = None

        # 데이터가 비어 있거나 없을 경우 (잘못된 종목 코드일 가능성)
        if history is None or history.empty:
            st.error(
                "주가 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해 주세요. "
                "(예: 삼성전자 005930.KS, 애플 AAPL)"
            )
        else:
            # -------------------------------------------
            # 현재가 및 1년 등락률 계산
            # -------------------------------------------
            first_price = history["Close"].iloc[0]   # 1년 전(기간 시작) 종가
            last_price = history["Close"].iloc[-1]    # 가장 최근 종가(현재가)

            change_amount = last_price - first_price
            change_percent = (change_amount / first_price) * 100

            # 종목 이름 가져오기 (없으면 입력한 코드 그대로 사용)
            try:
                company_name = stock.info.get("longName", ticker_symbol)
            except Exception:
                company_name = ticker_symbol

            st.subheader(f"🏢 {company_name} ({ticker_symbol})")

            # -------------------------------------------
            # 지표 카드 (현재가, 1년 등락률)
            # -------------------------------------------
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="현재가",
                    value=f"{last_price:,.2f}"
                )

            with col2:
                st.metric(
                    label="1년 등락률",
                    value=f"{change_percent:,.2f}%",
                    delta=f"{change_amount:,.2f}"
                )

            # -------------------------------------------
            # Plotly 꺾은선 그래프로 주가 흐름 표시
            # -------------------------------------------
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=history.index,
                    y=history["Close"],
                    mode="lines",
                    name="종가",
                    line=dict(color="#FFB703", width=2.5),  # 따뜻한 노란색 계열
                    fill="tozeroy",
                    fillcolor="rgba(255, 183, 3, 0.15)"
                )
            )

            fig.update_layout(
                title="최근 1년 주가 흐름",
                xaxis_title="날짜",
                yaxis_title="종가",
                template="plotly_white",
                hovermode="x unified",
                plot_bgcolor="#FFF8E7",   # 크림톤 배경
                paper_bgcolor="#FFF8E7",
                font=dict(size=14)
            )

            st.plotly_chart(fig, use_container_width=True)

            # 원본 데이터 표로 확인하고 싶은 사람을 위한 접기 메뉴
            with st.expander("원본 데이터 표 보기"):
                st.dataframe(history[["Open", "High", "Low", "Close", "Volume"]])

else:
    # 버튼을 아직 누르지 않았을 때 안내 문구
    st.info("종목 코드를 입력하고 '조회하기' 버튼을 눌러주세요.")
