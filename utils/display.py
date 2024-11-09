import streamlit as st
import random
from utils.youtube_api import search_comments, get_trending_videos, search_videos
from models.src.koBert_inf import main_analyze
import config.config as config
import json

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
    total = positive_count + neutral_count + negative_count
    if total > 0:
        totla=total+300
        st.markdown(
            """
            <div style="display: flex; width: 100%; height: 20px;">
                <div style="width: {positive}%; background-color: green; border-radius: 10px 0 0 10px;"></div>
                <div style="width: {neutral}%; background-color: gray;"></div>
                <div style="width: {negative}%; background-color: red; border-radius: 0 10px 10px 0;"></div>
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

    # 감정 분석 버튼 클릭 시 세션 상태를 변경하여 모달 창을 표시
    if st.button("감정 분석", key=f"analyze_{video['video_id']}"):
        # 감정 이모티콘 통계 이미지 표시
        emotions = {
            '행복': statistics.get('happiness', 0),
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
        #이모티콘 나타내기
        with st.expander("감정 분석 결과", expanded=True):
            st.markdown("<div style='text-align: center; display: flex; justify-content: space-around; align-items: center;'>", unsafe_allow_html=True)
            for emotion, count in emotions.items():
                st.markdown(
                    f"""
                    <div style='display: inline-block; text-align: center; margin: 5px; padding: 5px;'>
                        <div style='font-size: 40px;'>{emotion_icons[emotion]}</div>
                        <div style='font-size: 14px;'>{emotion}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.session_state.show_modal = True
        st.session_state.selected_video_id = video["video_id"]
        #st.rerun()  # 상태 변경 후 앱을 다시 렌더링


def show_modal():
    """모달 창 표시"""
    print("==============모달===========")
    video_id = st.session_state.get("selected_video_id", None)
    if st.session_state.get("show_modal", False):
        #comments = st.session_state.comments[video_id]
        #comments는  [{}, {}, {}] 형태이기에 next() 함수와 리스트 컴프리헨션을 사용
        gen = (item[video_id] for item in st.session_state.comments if video_id in item)
        comments = next(gen, [])  # 첫 번째 값을 추출하거나 없으면 빈 리스트 반환
        sentiments = [random.choice(["긍정", "부정"]) for _ in comments]

        # 모달 내용 구성
        modal_html = """
        <div id="overlay"></div>
        <div id="modal">
            <button onclick="document.getElementById('modal').style.display='none'; document.getElementById('overlay').style.display='none';">&#10006;</button>
            <h3>댓글 및 감정 분석 결과</h3>
            <ul>
        """
        for comment, sentiment in zip(comments, sentiments):
            modal_html += f"<li class='comment-text'><strong>댓글:</strong> {comment} | <strong>감정:</strong> {sentiment}</li>"

        modal_html += """
            </ul>
        </div>
        """

    # 모달 내용을 한 번에 출력
    if st.session_state.get("show_modal", False):
        st.markdown(modal_html, unsafe_allow_html=True)
        # 닫기 버튼
        if st.button("닫기", key=f"close_modal_{video_id}"):
            st.session_state.show_modal = False
            st.session_state.pop("selected_video_id", None)  # 상태 초기화
            st.experimental_rerun()  # UI를 즉시 갱신하여 모달을 닫음






def highlight_keywords(comment, positive_keywords, negative_keywords):
    # 키워드와 그에 해당하는 색상을 정의
    keyword_colors = {**dict.fromkeys(positive_keywords, 'red'), **dict.fromkeys(negative_keywords, 'blue')}

    # 키워드 강조
    for keyword, color in keyword_colors.items():
        comment = comment.replace(keyword, f"<strong style='color:{color};'>{keyword}</strong>")
    
    return comment


def show_comments(video_id, comment, statistics):
    """가장 많은 감정을 가진 5개의 대표 댓글을 표시합니다."""

    # 분석된 comments가 있는 json파일 읽음
    with open(f"data/analyzed_comments_{video_id}.json", "r", encoding="utf-8") as f:
        comments_data = json.load(f)

    # 가장 많은 감정 (긍정 부정 중립 중)이 무엇인지 찾아냄
    common_emotion = max(statistics, key=statistics.get)

    # 가장 많은 감정의 댓글을 뽑아냄
    selected_comments = [c for c in comments_data if c['emotion'] == common_emotion]

    # 그중 5개만 뽑아냄
    selected_comments = selected_comments[:5]

    # 감정별 아이콘 설정
    sentiment_icons = {
        "positive": "👍",
        "negative": "👎",
        "neutral": "😐"
    }

    positive_keywords = ['좋아요', '좋아', '좋다', '좋네', '사랑', '기쁘다', '기쁨', '고마워', '대박', '최고', '사랑해', '재밌어', '아름다워']
    negative_keywords = ['싫어요', '싫어', '싫다', '싫네', '나쁜', '슬퍼', '슬픔', '아니', '최악', '화가나', '실망', '별로']
    
    st.write("대표 댓글:")
    for comment_element in comment[video_id]:
        icon = sentiment_icons.get(comment['emotion'], "😐")
        st.markdown(
            f"""
            <div class='comment-container'>
                <span class='icon'>{icon}</span>
                <div class='comment-text'>{highlight_keywords(comment_element, positive_keywords, negative_keywords)}</div>
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

def show_search_results(videos, comments):
    # 동영상과 댓글을 세로로 나열하여 출력
    for video, comment in zip(videos, comments):
        with st.container():
            col_video, col_comments = st.columns([1, 2]) # 두 열 레이아웃 설정

            #comments들 수집 후 저장.
            #search_comments(video['video_id'])
            #comments들 분석 저장. statistics엔 감정별 통계가 포함되어있음.
            statistics=main_analyze(video)

            with col_video: # 왼쪽 열 - 비디오 정보 표시
                show_video_info(video,statistics)
            with col_comments: # 오른쪽 열 - 대표 댓글 표시
                show_comments(video["video_id"], comment, statistics)

