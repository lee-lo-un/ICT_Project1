from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEYS = [
    'YOUR_API_KEY_1',
    'YOUR_API_KEY_2',
    # 추가 API 키를 여기에 추가
]

current_key_index = 0

def get_youtube_service():
    """여러 API 키를 순차적으로 사용하여 YouTube API 서비스를 반환"""
    global current_key_index
    try:
        key = API_KEYS[current_key_index]
        return build('youtube', 'v3', developerKey=key)
    except HttpError as e:
        if 'quotaExceeded' in str(e):
            current_key_index = (current_key_index + 1) % len(API_KEYS)
            if current_key_index == 0:
                raise Exception("모든 API 키의 쿼터가 초과되었습니다.")
            return get_youtube_service()

# API 호출 예시 함수
def search_videos(query, max_results=5):
    youtube = get_youtube_service()
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        return response.get('items', [])
    except HttpError as e:
        raise Exception(f"API 호출 중 오류 발생: {e}")
