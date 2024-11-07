import streamlit as st
from utils.display import show_trending_videos, sidebar_options
import config.config as config

def show_home():
    """홈 페이지 함수"""
    # 사이드바 옵션 설정
    sidebar_options()
    st.subheader("유튜브 인기 급상승 동영상")
    
    num_video = config.POPULARITY_VIDEO_COUNT
    show_trending_videos(num_video)

# 페이지가 직접 실행될 때만 show_home() 호출
if __name__ == "__main__":
    show_home()
