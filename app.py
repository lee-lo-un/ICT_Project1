import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="mxnet.optimizer.optimizer")
import streamlit as st
from pages.home import show_home
from pages.search import show_search

def main():
    # 공통적인 레이아웃
    st.title("유튜브 댓글 감정 분석")
    
    # '홈으로' 버튼 추가
    if st.button("🏠 홈으로"):
        st.session_state.page = "Home"  # 홈 버튼 클릭 시 홈 페이지로 전환

    # 검색 기능 포함
    with st.form("search_form"):
        # 열을 나누어 입력창과 버튼 배치
        col1, col2 = st.columns([8, 1])
        with col1:
            query = st.text_input("검색어 입력창", key="query_input", placeholder="검색어를 입력하세요", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("검색")

    # 페이지 상태 초기화
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    # 페이지 전환 및 기능 실행
    if submit_button and query: #검색어가 입력되거나 검색 버튼 클릭 
        st.session_state.page = "Search"  # 검색 시 페이지 전환

    # 각 페이지에 따라 해당 함수를 호출
    if st.session_state.page == "Search" and query:
        show_search(query)  # 검색어를 인자로 전달
    elif st.session_state.page == "Home":
        show_home()

if __name__ == "__main__":
    main()
