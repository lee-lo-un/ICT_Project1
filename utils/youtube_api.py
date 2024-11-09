import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError  # 추가된 부분
import os
import json
import glob
import config.config as config 

# API 키 및 YouTube API 클라이언트 생성
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

def get_trending_videos(max_results):
    """유튜브 인기 급상승 동영상 정보 가져오기"""
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        chart="mostPopular",
        regionCode="KR", # 원하는 지역 코드 설정
        maxResults=max_results
    )
    response = request.execute()
    videos = []

    for item in response["items"]:
        video_id = item["id"]
        title = item["snippet"]["title"]
        thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"]
        tags = item["snippet"].get("tags", ["태그 없음"]) # 태그가 없으면 '태그 없음'으로 표시

        publish_date = item["snippet"]["publishedAt"]

        videos.append({
            "video_id": video_id,
            "title": title,
            "thumbnail_url": thumbnail_url,
            "tags": tags,
            "publishedAt": publish_date
        })

    return videos

def search_videos(query, year_range, month_start, month_end, max_results):
    """
    - 검색어(query)를 사용해 유튜브에서 상위 동영상 정보를 가져오기
      (상위 5개의 동영상 ID, 제목, 썸네일 URL 정보)
    - YouTube Data API를 사용하여 지정된 검색어로 동영상을 검색
    """
    request = youtube.search().list(
        part="snippet", # snippet 정보를 가져옵니다 (제목, 썸네일 등)
        q=query, # 검색어를 API 요청의 'q' 파라미터로 설정
        type="video", # 검색 유형을 'video'로 설정하여 동영상만 검색
        maxResults=max_results * 2  # 댓글이 비활성화된 영상을 제외하기 위해 더 많이 가져옴
    )
    # API 요청을 실행하고 응답을 받아오기
    response = request.execute()

    # 동영상 정보를 저장할 리스트 초기화
    videos = []

    # 응답에서 동영상 항목을 하나씩 반복하여 필요한 정보 추출
    for item in response["items"]:
        video_id = item["id"]["videoId"] # 동영상의 ID
        title = item["snippet"]["title"] # 동영상 제목
        thumbnail_url = item["snippet"]["thumbnails"]["high"]["url"] # 고해상도 썸네일 URL
        publish_date = item["snippet"]["publishedAt"] # 게시 연도
        
        # 게시 연도를 확인하여 연도 범위에 해당하는지 체크
        publish_year = int(publish_date[:4]) # 'YYYY-MM-DDTHH:MM:SSZ' 형식에서 연도 추출
        publish_month = int(publish_date[5:7])  # 월 추출
        if (year_range[0] <= publish_year <= year_range[1] 
            and month_start <= publish_month <= month_end): 
            # 댓글 활성화 여부 확인
            try:
                youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=1,
                    textFormat="plainText"
                ).execute()

                # 댓글 요청이 성공하면 해당 영상을 리스트에 추가
                videos.append({
                    "video_id": video_id,
                    "title": title,
                    "thumbnail_url": thumbnail_url,
                    "publish_date": publish_date
                })
                # 지정된 최대 결과 수에 도달하면 중단
                if len(videos) >= max_results:
                    break
            except HttpError as e:
                if e.resp.status == 403:
                    # 댓글이 비활성화된 경우 해당 비디오는 제외
                    continue

    return videos


def search_comments(video_id):
    """특정 동영상의 댓글을 최대 100개까지 가져와 data 폴더에 JSON 파일로 저장"""
    comments = {} # 댓글을 저장할 리스트 초기화

    # YouTube API를 통해 댓글 요청
    request = youtube.commentThreads().list(
        part="snippet", # snippet 정보를 가져옵니다 (댓글 내용 등)
        videoId=video_id, # 요청할 동영상 ID 설정
        maxResults=config.COMMENT_COUNT, # 최대 댓글 수 100개로 제한
        textFormat="plainText" # 댓글 형식을 일반 텍스트로 설정
    )
    response = request.execute()

    # 응답에서 각 댓글 항목을 반복하여 댓글 내용 추출
    for item in response["items"]:

        #comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        #comments.append(comment) # 댓글을 리스트에 추가
        video_id = item["snippet"]["videoId"]  # video ID 가져오기 (키로 사용)
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]

        # video_id를 키로 하여 댓글 리스트를 생성 또는 추가
        if video_id not in comments:
            comments[video_id] = []  # 키가 없으면 리스트 초기화
        comments[video_id].append(comment)  # 댓글 추가
    

    # 댓글을 JSON 파일로 저장 (파일명: data/comments_{video_id}.json)
    file_path = f"data/comments_{video_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=4)

    # 상위 5개의 댓글 반환

    return {video_id: comments[video_id][:5]}

