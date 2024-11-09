import streamlit as st
import random

from utils.youtube_api import search_comments, get_trending_videos, search_videos
from models.src.koBert_inf import main_analyze
import config.config as config
import json
import streamlit as st
from streamlit_modal import Modal


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

def show_emotion_bar_chart(positive_count, neutral_count, negative_count):
    """감정 비율을 막대 차트 형태로 표시합니다."""
    total = positive_count + neutral_count + negative_count+1
    
    if total > 0:
        total=total+300
        st.markdown(
            """
            <div style="display: flex; width: 100%; height: 20px;">
                <div style="width: {positive}%; background-color: green; border-radius: 10px;"></div>
                <div style="width: {neutral}%; background-color: transparent; border-radius: 10px;"></div>
                <div style="width: {negative}%; background-color: red; border-radius: 10px;"></div>
            </div>
            """.format(
                positive=(positive_count+100 / total) * 100,
                neutral=(neutral_count+100 / total) * 100,
                negative=(negative_count+100 / total) * 100
            ),
            unsafe_allow_html=True,
        )

def show_video_info(video, statistics):
    """비디오 정보 표시 및 감정 분석 버튼 제공"""
    
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
    
    #json파일 저장될 때 까지 기다림

    show_emotion_bar_chart(statistics['positive'], statistics['neutral'], statistics['negative'])
    temperature = statistics['positive'] - statistics['negative']+30
    st.write(f"🌡️ 온도: {temperature}")

def highlight_keywords(comment, positive_keywords, negative_keywords):
    # 키워드와 그에 해당하는 색상을 정의
    keyword_colors = {**dict.fromkeys(positive_keywords, 'red'), **dict.fromkeys(negative_keywords, 'blue')}

    # 키워드 강조
    for keyword, color in keyword_colors.items():
        comment = comment.replace(keyword, f"<strong style='color:{color};'>{keyword}</strong>")
    
    return comment

# 감정 이모티콘 통계 이미지 표시 함수
def make_emoji():
    with open(f"data/sum_comments_statistics.json", "r", encoding="utf-8") as f:
        statistics = json.load(f)

    emotions = {
        '행복': statistics.get('positive', 0),
        '공포': statistics.get('fear', 0),
        '놀람': statistics.get('surprise', 0),
        '분노': statistics.get('anger', 0),
        '슬픔': statistics.get('sadness', 0),
        '혐오': statistics.get('disgust', 0),
        '중립': statistics.get('neutral', 0)
    }

    emotion_icons = {
        '행복': '😊',
        '공포': '😨',
        '놀람': '😲',
        '분노': '😡',
        '슬픔': '😢',
        '혐오': '🤢',
        '중립': '😐'
    }

    # HTML 코드 생성
    emoji_html = """
        <div style='display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap;'>
    """

    for emotion, count in emotions.items():
        emoji_html += f"""
            <div style='text-align: center; margin: 10px;'>
                <div style='font-size: 40px;'>{emotion_icons[emotion]}</div>
                <div style='font-size: 14px; color: #555;'>{emotion} ({count})</div>
            </div>
        """

    emoji_html += "</div>"

    # Streamlit의 components.html을 사용해 HTML을 렌더링
    st.components.v1.html(emoji_html, height=150)


def show_comments(video_id, comment, statistics):
    """가장 많은 감정을 가진 5개의 대표 댓글을 표시합니다."""

    # 분석된 comments가 있는 json파일 읽음
    with open(f"data/analyzed_comments_{video_id}.json", "r", encoding="utf-8") as f:
        comments_data = json.load(f)

    #부정적인 감정이 많으면 negative로 설정
    if (statistics['negative']>statistics['positive']) and (statistics['negative']>statistics['neutral']):
        selected_comments = [c for c in comments_data if c['emotion'] in ["fear","surprise","anger","sadness","disgust"]]
    # 가장 많은 감정 (긍정 부정 중립 중)이 무엇인지 찾아냄
    # 가장 많은 감정의 댓글을 뽑아냄
    else:
        common_emotion = max(statistics, key=statistics.get)
        selected_comments = [c for c in comments_data if c['emotion'] == common_emotion]

    # 그중 5개만 뽑아냄
    selected_comments = selected_comments[:5]

    # 감정별 아이콘 설정
    sentiment_icons = {
        "positive": "👍",
        "negative": "👎",
        "neutral": "😐"
    }

    # 댓글을 나타냄
    st.write("대표 댓글:")
    for comment in selected_comments:
        icon = sentiment_icons.get(comment['emotion'], "😐")

        #부정적인 감정이 많으면 negative로 설정
        if comment['emotion'] in ["fear","surprise","anger","sadness","disgust"]:
            icon="👎"

        st.markdown(
            f"""
            <div class='comment-container'>
                <span class='icon'>{icon}</span>
                <div class='comment-text'>{comment['comment']}</div>
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
                        <img src='{video["thumbnail_url"]}' style='width:100%; border-radius:20px '>
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

def show_search_results(videos, comments):
    # Create the emoji column container first, separate from video and comments
    emoji_container = st.container()  # Container for the emoji to make sure it appears in a specific location

    # Display videos and comments
    for video, comment in zip(videos, comments):
        # Create two columns for each video
        col_video, col_comments = st.columns([3, 4])  # Set two columns for video and comments

        # Collect comments and save them. Save comments analysis.
        # statistics contains emotion analysis results for each video
        statistics = main_analyze(video)

        with col_video:  # Left column - display video information
            show_video_info(video, statistics)

        with col_comments:  # Right column - display representative comments
            show_comments(video["video_id"], comment, statistics)

        # Add a horizontal separator to differentiate between each video's results
        st.write("---")

    # After the loop is finished, display emojis in the emoji container at the top
    with emoji_container:
        make_emoji()



