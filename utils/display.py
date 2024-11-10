import streamlit as st
import random

from utils.youtube_api import search_comments, get_trending_videos, search_videos
from models.src.koBert_inf import main_analyze
import config.config as config
import json
import streamlit as st
from utils.data_handle import get_top_words

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
        
        # 월을 숫자로 변환하여 반환
        month_start_num = int(month_start[:-1])
        month_end_num = int(month_end[:-1])

    return no_of_results, year_range, (month_start_num, month_end_num)

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
    publish_date = video.get('publish_date', '0000-00-00')
    publish_year = publish_date[:4]
    publish_month = publish_date[5:7]
    publish_day = publish_date[8:10]
    title = video.get("title", "제목 없음")
    tags = video.get('tags', [])
    tags_display = ", ".join(tags[:5]) if isinstance(tags, list) else "태그 없음"

    # 썸네일과 제목을 링크로 표시 (제목 크기 및 높이 고정)
    st.markdown(
        f"""
        <a href='https://www.youtube.com/watch?v={video['video_id']}' target='_blank'>
            <img src='{video['thumbnail_url']}' class="thumbnail">
        </a>
        """, unsafe_allow_html=True
    )
    # st.write(
    #     f"""
    #     <div class="video-title2">
    #         {video['title']}
    #     </div>
    #     """, unsafe_allow_html=True
    # )

    # 제목과 날짜 표시
    st.markdown(
        f"""
        <div>
            <div class='video-title2'>
                {title}
            </div>
            <p><strong>{publish_year}년 {publish_month}월 {publish_day}일</strong></p>
        </div>
        """, unsafe_allow_html=True
    )
    
    #json파일 저장될 때 까지 기다림

    show_emotion_bar_chart(statistics['positive'], statistics['neutral'], statistics['anger'])
    # 체온 37을 기준 
    temperature = 37 + statistics['positive'] - statistics['anger']
    print("온도:",temperature,"statistics['positive']:",statistics['positive'],"statistics['negative']:",statistics['negative'])
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

    positive_keywords = ['좋아요', '좋아', '좋다', '좋고', '좋네', '사랑', '기쁘다', '기쁨', '고마워', '대박', '최고', '사랑해', '재밌어', '아름다워', '응원', '위로', '희망', '소망', '밝음', '']
    negative_keywords = ['싫어요', '싫어', '싫다', '싫고', '싫네', '나쁜', '나쁨', '슬퍼', '슬픔', '아니', '최악', '화가나', '실망', '별로', '한심', '똥인지', '저런걸', '에라이', '절망', '비관', '박탈']

    # 댓글을 나타냄
    st.write("대표 댓글:")
    for comment in selected_comments:
        icon = sentiment_icons.get(comment['emotion'], "😐")

        #부정적인 감정이 많으면 negative로 설정
        if comment['emotion'] in ["anger"]:
            icon="👎"

        st.markdown(
            f"""
            <div class='comment-container'>
                <span class='icon'>{icon}</span>
                <div class='comment-text'>{highlight_keywords(comment['comment'], positive_keywords, negative_keywords)}</div>
            </div>
            """, unsafe_allow_html=True
        )
    st.write("---")

# 유튜브 인기 급상승 동영상 
def show_trending_videos(num_video):
    videos = get_trending_videos(num_video)
    
    if not videos:  # videos가 None이거나 빈 리스트인 경우 예외 처리
        st.warning("트렌딩 비디오를 가져오는 데 실패했습니다.")
        return

    # 동영상 데이터를 3개씩 나누어 열에 배치
    for i in range(0, len(videos), 3):
        cols = st.columns(3)  # 3개의 열 생성
        for j, video in enumerate(videos[i:i + 3]):
            with cols[j]:  # 각 열에 동영상 정보 표시
                # 날짜 추출 및 기본값 설정
                publish_date = video.get('publishedAt', '0000-00-00')
                publish_year = publish_date[:4]
                publish_month = publish_date[5:7]
                publish_day = publish_date[8:10]

                # 비디오 ID, 썸네일 URL, 제목, 태그 등 기본값 처리
                video_id = video.get("video_id", "unknown")
                thumbnail_url = video.get("thumbnail_url", "")
                title = video.get("title", "제목 없음")
                tags = video.get('tags', [])
                tags_display = ", ".join(tags[:5]) if isinstance(tags, list) else "태그 없음"

                # 비디오 정보 표시
                st.markdown(
                    f"""
                    <a href='https://www.youtube.com/watch?v={video_id}' target='_blank'>
                        <img src='{thumbnail_url}' style='width:100%; border-radius:20px '>
                    </a>
                    """, unsafe_allow_html=True
                )

                # 제목과 날짜 표시
                st.markdown(
                    f"""
                    <div>
                        <div class='video-title2'>
                            {title}
                        </div>
                        <p><strong>{publish_year}년 {publish_month}월 {publish_day}일</strong></p>
                        <p>관련 태그: {tags_display}</p>
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

        # 댓글에서 가장 많이 등장한 단어 5개 추출
        top_words = get_top_words(comment[video["video_id"]], config.NUM_TOP_WORDS)
            
        # 결과 출력
        # for word, count in top_words:
        #     st.text(f"{word}: {count}번")
    
        # 댓글 감정분석
        #st.text(display_emotion_chart_scaled(statistics))
        # 감정 데이터와 시각화 출력

        # 'negative' 항목 제거
        if 'negative' in statistics:
            del statistics['negative']

         # 댓글 top7 출력
        word_counts_text = ', '.join([f"{word}({count})" for word, count in top_words])
        formatted_text = format_word_counts(word_counts_text)
        st.markdown(formatted_text, unsafe_allow_html=True)   
        
        # Streamlit에서 마크다운과 HTML을 사용하여 출력
        st.markdown(
            f"""
            <div style="font-size: 18px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                {display_emotion_chart_scaled(statistics)}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Add a horizontal separator to differentiate between each video's results
        st.write("---")

    # After the loop is finished, display emojis in the emoji container at the top
    with emoji_container:
        make_emoji()

def format_word_counts(word_counts_text):
    # 단어와 숫자를 나누어 스타일 지정
    formatted_text = ""
    for item in word_counts_text.split(', '):
        if '(' in item and ')' in item:  # 괄호로 숫자가 있는지 확인
            word, count = item.split('(')  # 괄호 앞뒤로 분리
            count = count.rstrip(')')  # 숫자 뒤의 닫는 괄호 제거
            formatted_text += f"<span style='font-size:20px; color:blue;'>{word.strip()}</span> <span style='font-size:16px; color:gray;'>({count})</span>, "
        else:
            formatted_text += f"<span style='font-size:20px; color:blue;'>{item.strip()}</span>, "  # 숫자가 없는 경우
    
    # 마지막 ', ' 제거 후 반환
    return formatted_text.rstrip(', ')

def display_emotion_chart_scaled(emotion_data, max_bar_length=24):
    # 전체 값의 합계를 계산하여 비율을 구함
    total = sum(emotion_data.values())
    
    # 기호 정의
    symbols = {
        'neutral': '⬛',
        'positive': '🟩',
        'anger': '🟥',
        'fear': '🟦',
        'surprise': '🟨',
        'sadness': '🟪',
        'disgust': '🟫'
    }
    

    # 가장 긴 감정명 길이를 구하여 정렬 기준 설정
    max_emotion_length = max(len(emotion) for emotion in emotion_data.keys())
    chart_lines = []
    
    for emotion, count in emotion_data.items():
        # 비율을 계산하여 출력 길이를 조정
        scaled_length = int((count / total) * max_bar_length) if total > 0 else 0
        
        # 감정에 해당하는 기호를 scaled_length만큼 반복하여 출력
        if emotion in symbols:
            bar = symbols[emotion] * scaled_length
            # 감정명 길이를 기준으로 공백을 추가해 정렬
            emotion_display = f"{emotion}({count}){' ' * (max_emotion_length - len(emotion))}:"
            chart_lines.append(f"{emotion_display} {bar}")
    
    # 각 줄을 줄바꿈 없이 출력
    return '<br>'.join(chart_lines)

def display_emotion_chart_scaled(emotion_data, max_bar_length=35):
    # 전체 값의 합계를 계산하여 비율을 구함
    total = sum(emotion_data.values())
    chart_lines = []

    # 감정 아이콘 및 기호 정의
    emotion_details = {
        '중립': {'icon': '😐', 'symbol': '⬛'},
        '행복': {'icon': '😊', 'symbol': '🟩'},
        '분노': {'icon': '😡', 'symbol': '🟥'},
        '혐오': {'icon': '🤢', 'symbol': '🟫'},
        '공포': {'icon': '😨', 'symbol': '🟦'},
        '놀람': {'icon': '😲', 'symbol': '🟨'},
        '슬픔': {'icon': '😢', 'symbol': '🟪'},
    }

    emotion_translation = {
    'neutral': '중립',
    'positive': '행복',
    'anger': '분노',
    'disgust': '혐오',
    'fear': '공포',
    'surprise': '놀람',
    'sadness': '슬픔',
    }

    for eng_emotion, count in emotion_data.items():
        # 영어 키를 한글로 변환
        emotion = emotion_translation.get(eng_emotion, eng_emotion)

        # 비율을 계산하여 출력 길이를 조정
        scaled_length = int((count / total) * max_bar_length) if total > 0 else 0

        # 감정 아이콘과 기호를 사용하여 출력
        if emotion in emotion_details:
            icon = emotion_details[emotion]['icon']
            symbol = emotion_details[emotion]['symbol']
            bar = symbol * scaled_length
            emotion_display = f"{icon} {emotion}({count}):"
            chart_lines.append(f"{emotion_display} {bar}")

    # 각 줄을 줄바꿈하여 반환
    return '<br>'.join(chart_lines)

