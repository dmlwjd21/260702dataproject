"""
Home.py — 멀티페이지 앱의 진입점(랜딩 페이지)
실제 대시보드는 pages/01_인구분석.py 에 있습니다.
"""

import streamlit as st

st.set_page_config(
    page_title="🏫 정보·데이터분석·AI 수업 자료실",
    page_icon="🏫",
    layout="wide",
)

st.title("🏫 정보 · 데이터분석 · 인공지능 수업 자료실")
st.markdown(
    """
안녕하세요! 👋 왼쪽 사이드바에서 페이지를 선택해주세요.


---
💡 사이드바가 안 보이면 화면 왼쪽 위의 `>` 아이콘을 눌러 펼쳐주세요.
"""
)
