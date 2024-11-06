import streamlit as st
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json
import os
import glob
import random

# .env 파일 로드 (환경 변수 파일을 불러와 API 키를 사용하도록 설정)
load_dotenv()

# API 키 가져오기 (환경 변수에서 YOUTUBE_API_KEY 값 가져옴)
API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# YouTube API 클라이언트 생성 (API 요청을 위한 클라이언트 객체 생성)
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def clear_data_folder():
    """data 폴더 내 모든 JSON 파일 삭제"""
    if not os.path.exists("data"):
        os.makedirs("data")
    else:
        files = glob.glob("data/*.json")
        for f in files:
            os.remove(f)

def search_videos(query, max_results=5):
    """
    검색어(query)를 사용해 유튜브에서 상위 동영상 정보를 가져옵니다.
    - YouTube Data API를 사용하여 지정된 검색어로 동영상을 검색
    - 상위 5개의 동영상 ID, 제목, 썸네일 URL 정보를 가져옵니다.
    """
    # YouTube API를 통해 검색 요청을 만듭니다.
    request = youtube.search().list(
        part="snippet",  # snippet 정보를 가져옵니다 (제목, 썸네일 등)
        q=query,  # 검색어를 API 요청의 'q' 파라미터로 설정
        type="video",  # 검색 유형을 'video'로 설정하여 동영상만 검색
        maxResults=max_results  # 검색 결과의 최대 개수를 5로 제한
    )
    
    # API 요청을 실행하고 응답을 받아옵니다.
    response = request.execute()

    # 동영상 정보를 저장할 리스트 초기화
    videos = []
    
    # 응답에서 동영상 항목을 하나씩 반복하여 필요한 정보 추출
    for item in response["items"]:
        video_id = item["id"]["videoId"]  # 동영상의 ID
        title = item["snippet"]["title"]  # 동영상 제목
        thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"]  # 고해상도 썸네일 URL

        # 동영상 정보를 딕셔너리로 정리하여 리스트에 추가
        videos.append({
            "video_id": video_id,
            "title": title,
            "thumbnail_url": thumbnail_url
        })

    # 최종적으로 상위 5개의 동영상 정보가 담긴 리스트 반환
    return videos

def get_and_save_comments(video_id):
    """특정 동영상의 댓글을 최대 100개까지 가져와 data 폴더에 JSON 파일로 저장"""
    comments = []  # 댓글을 저장할 리스트 초기화

    # YouTube API를 통해 댓글 요청을 만듭니다.
    request = youtube.commentThreads().list(
        part="snippet",  # snippet 정보를 가져옵니다 (댓글 내용 등)
        videoId=video_id,  # 요청할 동영상 ID 설정
        maxResults=100,  # 최대 댓글 수 100개로 제한
        textFormat="plainText"  # 댓글 형식을 일반 텍스트로 설정
    )
    
    # API 요청을 실행하고 응답을 받아옵니다.
    response = request.execute()

    # 응답에서 각 댓글 항목을 반복하여 댓글 내용 추출
    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)  # 댓글을 리스트에 추가
    
    # 댓글을 JSON 파일로 저장 (파일명: data/comments_{video_id}.json)
    file_path = f"data/comments_{video_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=4)
    
    # 상위 5개의 댓글 반환
    return comments[:5]


def sidebar_options():
    """사이드바에서 검색 옵션을 설정하고 반환합니다."""
    with st.sidebar:
        st.header("Search Options")
        
        # 결과 개수 설정 (최대값 5로 제한)
        no_of_results = st.number_input(
            "Number of results", min_value=1, max_value=5, value=5, format="%i"
        )
        
        # 필터 설정
        st.subheader("Filters")

        # 연도 범위 선택 슬라이더
        year_range = st.slider("Year", 2005, 2025, (2005, 2025))
        
        # 평점 입력
        rating = st.number_input("Rating", 0.0, 10.0, 0.0, step=1.0)
        
    # 선택한 옵션 반환
    return no_of_results, year_range, rating

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
        <div class="video-title">
            {video['title']}
        </div>
        """, unsafe_allow_html=True
        )

    # 임의의 온도 값을 생성하여 온도계 아이콘과 함께 표시
    temperature = random.randint(0, 100)
    st.write(f"🌡️ 온도: {temperature}")

    # 감정 분석 버튼 (고유 키를 설정하여 버튼 중복 오류 방지)
    st.button("감정 분석", key=f"analyze_{video['video_id']}")

def show_comments(video_id):
    """대표 댓글 5개와 랜덤 감정 아이콘 표시"""
    comments = get_and_save_comments(video_id)
    
    # 감정 아이콘 리스트
    sentiment_icons = {
        "좋다": "👍",
        "나쁘다": "👎",
        "보통이다": "😐"
    }
    
    st.write("대표 댓글:")
    for comment in comments:
        # 랜덤으로 감정 선택
        sentiment = random.choice(list(sentiment_icons.keys()))
        icon = sentiment_icons[sentiment]
        
        # 댓글을 아이콘과 함께 표시
        st.markdown(
            f"""
            <div class='comment-container'>
                <span class='icon'>{icon}</span>
                <div class='comment-text'>{comment}</div>
            </div>
            """, unsafe_allow_html=True
        )
    
    st.write("---")

# 스타일 설정
st.markdown(
    """
    <style>
    
    .stTextInput, .stButton {
        height: 38px;
    }

    .video-title {
        font-size: 16px;
        font-weight: bold;
        height: 50px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .thumbnail {
        width: 100%;
    }

    .comment-container {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .icon {
        font-size: 20px;
        margin-right: 8px;
    }
    .comment-text {
        width: 100%;
        height: 60px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;

    </style>
    """, unsafe_allow_html=True
)

def main():
     
    max_results, year_range, rating = sidebar_options()

    st.title("유튜브 댓글 감정 분석")
    
    # 검색창과 버튼을 가로로 배치하여 form 안에 넣기
    with st.form("search_form"):
        # 열을 나누어 입력창과 버튼을 각각 배치
        col1, col2 = st.columns([8, 1])  # col1이 더 넓게 설정됨
        with col1:
            query = st.text_input("검색어 입력창", key="query_input", placeholder="검색어를 입력하세요", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button("검색")

    # 검색어가 입력되거나 검색 버튼을 클릭했을 때 검색 실행
    if query and submit_button:
        # 기존 JSON 파일 삭제
        clear_data_folder()
        
        # 검색어와 옵션을 사용하여 상위 동영상 검색
        videos = search_videos(query, max_results)

        # 동영상과 댓글을 세로로 나열하여 출력
        for video in videos:
            with st.container():
                # 두 열 레이아웃 설정
                col_video, col_comments = st.columns([1, 2])
                
                # 왼쪽 열 - 비디오 정보 표시
                with col_video:
                    show_video_info(video)
                
                # 오른쪽 열 - 대표 댓글 표시
                with col_comments:
                    show_comments(video["video_id"])

if __name__ == "__main__":
    main()
