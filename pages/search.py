import streamlit as st
from utils.display import show_search_results, sidebar_options
from utils.youtube_api import clear_data_folder
from utils.styles import set_global_styles

def show_search(query):
    """검색 페이지 함수"""
    set_global_styles()
    # 사이드바 옵션 설정
    max_results, year_range, (month_start_num, month_end_num), rating = sidebar_options()

    # 검색어가 입력되었을 때 결과 표시
    if query:
        # 기존 JSON 파일 삭제
        clear_data_folder()
        st.write(f"검색어: **{query}**")
        # 검색 실행
        show_search_results(query, year_range, month_start_num, month_end_num,max_results)

# 페이지가 직접 실행될 때만 show_search() 호출 (테스트용)
if __name__ == "__main__":
    show_search("테스트 검색어")