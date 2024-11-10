import streamlit as st
from utils.display import show_trending_videos, sidebar_options
import config.config as config

def show_home():
    """홈 페이지 함수"""
    # 사이드바 옵션 설정
    sidebar_options()
    st.subheader("유튜브 인기 급상승 동영상")

    if 'home_page_loaded' not in st.session_state:
        st.session_state.home_page_loaded = False  # 초기화
    
    # 세션 상태를 사용하여 첫 요청 여부를 관리
    if not st.session_state.home_page_loaded:
        num_video = config.POPULARITY_VIDEO_COUNT
        show_trending_videos(num_video)
        st.session_state.home_page_loaded = True
        print("Home page loaded for the first time.")
    else:
        st.write("이미 인기 급상승 동영상이 로드되었습니다.")

# 페이지가 직접 실행될 때만 show_home() 호출
if __name__ == "__main__":
    show_home()
