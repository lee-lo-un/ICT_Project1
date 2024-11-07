import streamlit as st
import random
from utils.youtube_api import get_and_save_comments, get_trending_videos, search_videos
import config.config as config

def sidebar_options():
    """사이드바에서 검색 옵션을 설정하고 반환합니다."""
    with st.sidebar:
        st.header("Search Options")

        # 결과 개수 설정 (최대값 5로 제한)
        no_of_results = st.number_input(
            "Number of results", min_value=1, max_value=5, value=config.VIDEO_SEARCH_COUNT, format="%i"
        )

        st.subheader("Filters")  # 필터 설정

        # 연도와 월을 하나의 영역으로 묶음
        with st.container():
            st.write("Date Filters")
            
            # 연도 범위 선택 슬라이더
            year_range = st.slider("Year", 2005, 2025, (2005, 2025))
            
            # 월 선택 (1월부터 12월까지)
            col1, col2 = st.columns(2)
            with col1:
                month_start = st.selectbox("Start Month", [f"{i}월" for i in range(1, 13)], index=0)
            with col2:
                month_end = st.selectbox("End Month", [f"{i}월" for i in range(1, 13)], index=11)

        # 평점 입력
        rating = st.number_input("Rating", 0.0, 10.0, 0.0, step=1.0)
        
        # 월을 숫자로 변환하여 반환
        month_start_num = int(month_start[:-1])
        month_end_num = int(month_end[:-1])

    return no_of_results, year_range, (month_start_num, month_end_num), rating

def show_video_info(video):
    """썸네일, 제목, 온도계, 감정 분석 버튼을 출력"""
    
    # 썸네일과 제목을 링크로 표시 (제목 크기 및 높이 고정)
    st.markdown(
        f"""
        <a href='https://www.youtube.com/watch?v={video['video_id']}' target='_blank'>
            <img src='{video['thumbnail_url']}' class="thumbnail">
        </a>
        """, unsafe_allow_html=True
    )
    st.write(
        f"""
        <div class="video-title2">
            {video['title']}
        </div>
        """, unsafe_allow_html=True
    )
    temperature = random.randint(0, 100)
    st.write(f"🌡️ 온도: {temperature}")
    st.button("감정 분석", key=f"analyze_{video['video_id']}")

def show_comments(video_id):
    """대표 댓글 5개와 랜덤 감정 아이콘 표시"""
    comments = get_and_save_comments(video_id)
    sentiment_icons = {
        "좋다": "👍",
        "나쁘다": "👎",
        "보통이다": "😐"
    }
    
    st.write("대표 댓글:")
    for comment in comments:
        sentiment = random.choice(list(sentiment_icons.keys()))
        icon = sentiment_icons[sentiment]
        st.markdown(
            f"""
            <div class='comment-container'>
                <span class='icon'>{icon}</span>
                <div class='comment-text'>{comment}</div>
            </div>
            """, unsafe_allow_html=True
        )
    st.write("---")

# 유튜브 인기 급상승 동영상 
def show_trending_videos(num_video):
    videos = get_trending_videos(num_video)
    # 동영상 데이터를 3개씩 나누어 열에 배치
    for i in range(0, len(videos), 3):
        cols = st.columns(3) # 3개의 열 생성
        for j, video in enumerate(videos[i:i + 3]):
            with cols[j]: # 각 열에 동영상 정보 표시
                # 날자 추출
                publish_date = video['publishedAt']  # 'YYYY-MM-DDTHH:MM:SSZ' 형식
                publish_year = publish_date[:4]  # 연도 추출
                publish_month = publish_date[5:7]  # 달 추출
                publish_day = publish_date[8:10]  # 일 추출

                st.markdown(
                    f"""
                    <a href='https://www.youtube.com/watch?v={video["video_id"]}' target='_blank'>
                        <img src='{video["thumbnail_url"]}' style='width:100%;'>
                    </a>
                    """, unsafe_allow_html=True
                )
                #st.write(f"**{publish_year}년 {publish_month}월 {publish_day}일**")  # 게시년도와 달 표시
                #st.write(f"**{video['title']}**")

                # 제목과 날짜 표시 (고정 높이 및 스타일 설정)
                st.markdown(
                    f"""
                    <div>
                        <div class='video-title2'>
                            {video['title']}
                        </div>
                        <p><strong>{publish_year}년 {publish_month}월 {publish_day}일</strong></p>
                        <p>관련 태그: {", ".join(video['tags'][:5])}</p>
                    </div>
                    """, unsafe_allow_html=True
                )

def show_search_results(query, year_range, month_start_num, month_end_num,max_results):
    # 검색어와 옵션을 사용하여 상위 동영상 검색
    videos = search_videos(query, year_range, month_start_num, month_end_num, max_results)

    # 동영상과 댓글을 세로로 나열하여 출력
    for video in videos:
        with st.container():
            col_video, col_comments = st.columns([1, 2]) # 두 열 레이아웃 설정
            with col_video: # 왼쪽 열 - 비디오 정보 표시
                show_video_info(video)
            with col_comments: # 오른쪽 열 - 대표 댓글 표시
                show_comments(video["video_id"])
