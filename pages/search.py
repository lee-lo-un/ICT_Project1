import streamlit as st
from utils.display import show_search_results, sidebar_options
from utils.youtube_api import clear_data_folder, search_videos, search_comments
from utils.styles import set_global_styles

def initialize_session_state():

    if 'comments' not in st.session_state:
        st.session_state['comments'] = []
    if 'videos' not in st.session_state:
        st.session_state.videos = []  # 검색 결과 초기화
    if 'selected_video_id' not in st.session_state:
        st.session_state.selected_video_id = None  # 선택된 비디오 ID 초기화
    if 'query_executed' not in st.session_state:
        st.session_state.query_executed = False  # 검색 실행 상태 초기화
    

def show_search(query):
    """검색 페이지 함수"""
    set_global_styles()
    initialize_session_state()  # 세션 상태 초기화

    max_results, year_range, (month_start_num, month_end_num), rating = sidebar_options()

    # 검색어가 입력되었을 때 실행
    if query:
        # 새로운 검색어가 입력되면 query_executed를 False로 초기화
        if 'previous_query' not in st.session_state or st.session_state.previous_query != query:
            st.session_state.query_executed = False
            st.session_state.previous_query = query

        if not st.session_state.get('query_executed', False):
            # 기존 JSON 파일 삭제 및 새로운 검색 결과 저장
            clear_data_folder()
            st.session_state.query_executed = True
            st.session_state.videos = search_videos(query, year_range, month_start_num, month_end_num, max_results)
            st.session_state.comments = [search_comments(video["video_id"]) for video in st.session_state.videos]
    
        # 검색 결과 표시
        if st.session_state.videos:
            show_search_results(st.session_state.videos, st.session_state.comments)
        else:
            st.write("검색 결과가 없습니다.")


# 페이지가 직접 실행될 때만 show_search() 호출 (테스트용)
if __name__ == "__main__":
    show_search("테스트 검색어")