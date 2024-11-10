from konlpy.tag import Okt
from collections import Counter
import concurrent.futures

#Okt 객체 생성
okt = Okt()

def analyze_comment(comment, korean_stopwords):
    # 형태소 분석 후 품사 태깅
    tokens_with_pos = okt.pos(comment, stem=True)  # pos() 메서드로 품사 태깅
    filtered_words = [word for word, pos in tokens_with_pos 
                      if pos in ['Noun', 'Verb', 'Adjective', 'ProperNoun', 'Foreign'] 
                      and word not in korean_stopwords 
                      and len(word) > 1]
    return filtered_words

def get_top_words(comments_dict, num_top_words):
    #불용어
    korean_stopwords = {
    '하다', '되다', '이렇다', '그렇다', '저렇다', '같다', '어떻다', '있다', '없다',
    '모든', '각', '몇', '다수', '조금', '많다', '때문', '이후', '전후', '동안',
    '이제', '다', '모두', '전부', '하나', '둘', '셋', '넷', '어디', '무엇', '왜',
    '어느', '하는', '이다', '같아요', '이라는'
    }


    # 모든 댓글을 병렬 처리
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda comment: analyze_comment(comment, korean_stopwords), comments_dict))

    # 모든 결과를 하나의 리스트로 합침
    all_tokens = [token for sublist in results for token in sublist]

    # 각 단어의 빈도 계산
    word_counts = Counter(all_tokens)

    # 가장 많이 등장한 단어 num_top_words개 추출
    top_words = word_counts.most_common(num_top_words)

    return top_words