import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="mxnet.optimizer.optimizer")
import streamlit as st
from pages.home import show_home
from pages.search import show_search
import streamlit as st
import torch
from models.src.koBert_inf import load_model

# 초기화 시 장치 설정
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# 모델을 한 번만 로드
if "model" not in st.session_state:
    st.session_state.model = load_model(device)
    print("Model loaded successfully.")

def main():
    # 공통적인 레이아웃
    st.title("사건의 시선")

     # 페이지 상태 초기화 (앱 처음 실행 시)
    if 'page' not in st.session_state:
        st.session_state.page = "Home"
    if 'home_page_loaded' not in st.session_state:
        st.session_state.home_page_loaded = False
    
    # '홈으로' 버튼 추가
    if st.button("🏠 홈으로"):
        st.session_state.page = "Home"  # 홈 버튼 클릭 시 홈 페이지로 전환
        st.session_state.home_page_loaded = False  # 홈으로 돌아갈 때 초기화

    # 검색 기능 포함
    with st.form("search_form"):
        # 열을 나누어 입력창과 버튼 배치
        col1, col2 = st.columns([8, 1])
        with col1:
            query = st.text_input("검색어 입력창", key="query_input", placeholder="검색어를 입력하세요", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("검색")

    # 페이지 전환 및 기능 실행
    if submit_button and query:  # 검색어가 입력되거나 검색 버튼 클릭 
        st.session_state.page = "Search"  # 검색 시 페이지 전환

    # 각 페이지에 따라 해당 함수를 호출
    if st.session_state.page == "Search" and query:
        print("Navigating to Search page")
        show_search(query)
    elif st.session_state.page == "Home":
        if not st.session_state.home_page_loaded:
            print("Navigating to Home page")
            show_home()
            st.session_state.home_page_loaded = True  # 첫 로드 이후에는 다시 로드되지 않음

if __name__ == "__main__":
    main()