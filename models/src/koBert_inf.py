import streamlit as st
import torch  
from torch.utils.data import Dataset, DataLoader  
from transformers import BertTokenizer, BertForSequenceClassification, AdamW  
from sklearn.model_selection import train_test_split  
import pandas as pd  
from torch import nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
from tqdm import tqdm, tqdm_notebook
from kobert_tokenizer import KoBERTTokenizer
from transformers import BertModel
from transformers.optimization import get_cosine_schedule_with_warmup
import gluonnlp as nlp
import json
import os
import gc

## infer setup
device = torch.device("cuda:0")
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(tokenizer.vocab_file, padding_token='[PAD]')
tok = nlp.data.BERTSPTokenizer(tokenizer, vocab, lower = False)
max_len = 64
batch_size = 64
tok = tokenizer.tokenize

def load_model(device):
    """BERT 모델과 가중치를 로드하는 함수"""
    bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
    model = BERTClassifier(bertmodel, dr_rate=0.3).to(device)
    
    ## 최초의 한번 실행 가중치 업데이트
    # state_dict = torch.load('models/weight/kobert241107.pth')
    # if "bert.embeddings.position_ids" not in state_dict:
    #     state_dict["bert.embeddings.position_ids"] = torch.arange(0, 512).expand((1, -1))
    # torch.save(state_dict, 'models/weight/kobert241107_updated.pth')
    model.load_state_dict(torch.load('models/weight/kobert241107_updated.pth'))

    return model

class BERTDataset(Dataset):
    def __init__(self, dataset, sent_idx, label_idx, bert_tokenizer, vocab, max_len,
                 pad, pair):
        transform = nlp.data.BERTSentenceTransform(
            bert_tokenizer, max_seq_length=max_len, vocab=vocab, pad=pad, pair=pair)

        self.sentences = [transform([i[sent_idx]]) for i in dataset]
        self.labels = [np.int32(i[label_idx]) for i in dataset]

    def __getitem__(self, i):
        return (self.sentences[i] + (self.labels[i], ))

    def __len__(self):
        return (len(self.labels))

class BERTClassifier(nn.Module):
    def __init__(self,
                 bert,
                 hidden_size=768,
                 num_classes=7,
                 dr_rate=None,
                 params=None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate

        self.classifier = nn.Linear(hidden_size, num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p=dr_rate)

    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)

        _, pooler = self.bert(input_ids=token_ids,
                              token_type_ids=segment_ids.long(),
                              attention_mask=attention_mask.float().to(token_ids.device),
                              return_dict=False)
        if self.dr_rate:
            out = self.dropout(pooler)
        return self.classifier(out)


def inference(predict_sentence):
    model = st.session_state.model
    model.eval()
    data = [predict_sentence, '0']
    dataset_another = [data]

    another_test = BERTDataset(dataset_another, 0, 1, tok, vocab, max_len, True, False)
    test_dataloader = torch.utils.data.DataLoader(another_test, batch_size=batch_size, num_workers=0)  # num_workers 수정

    test_eval = ""
    score = 0.00
    with torch.no_grad():  # no_grad는 그래디언트 계산을 막아줌
        for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
            token_ids = token_ids.long().to(device)
            segment_ids = segment_ids.long().to(device)

            # 유효 길이와 레이블도 GPU에 올림
            valid_length = valid_length
            label = label.long().to(device)

            # GPU 메모리 최적화를 위해 캐시 비우기
            out = model(token_ids, valid_length, segment_ids)

        for i in out: # out = model(token_ids, valid_length, segment_ids)
            logits = i
            logits = logits.detach().cpu().numpy()

            emotion = np.argmax(logits)
            if emotion == 0:
                test_eval="fear"
            elif emotion == 1:
                test_eval="surprise"
            elif emotion == 2:
                test_eval="anger"
            elif emotion == 3:
                test_eval="sadness"
            elif emotion == 4:
                test_eval="neutral"
            elif emotion == 5:
                test_eval="positive"
            elif emotion == 6:
                test_eval="disgust"

    return test_eval

#분류한 json파일을 불러와 통계를 낸다
def generate_statistics(video):
    #넘겨받은 video_id를 통해 json파일을 구별하고 통계를 낸다
    analyzed_file_path = f"data/analyzed_comments_{video['video_id']}.json"
    if not os.path.exists(analyzed_file_path):
        raise FileNotFoundError(f"Analyzed results for video ID {video['video_id']} not found.")

    with open(analyzed_file_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    #각 감정을 count한다
    positive_count = sum(1 for result in results if result["emotion"] == "positive")
    neutral_count = sum(1 for result in results if result["emotion"] == "neutral")
    negative_count = sum(1 for result in results if result["emotion"] in ["fear", "anger", "disgust"])
    fear_count = sum(1 for result in results if result["emotion"] == "fear")
    surprise_count = sum(1 for result in results if result["emotion"] == "surprise")
    anger_count = sum(1 for result in results if result["emotion"] == "anger")
    sadness_count = sum(1 for result in results if result["emotion"] == "sadness")
    disgust_count = sum(1 for result in results if result["emotion"] == "disgust")

    #감정 통계 결과를 '감정':'수' 로 저장
    statistics = {
        "positive": positive_count,
        "neutral": neutral_count,
        "negative": negative_count,
        "fear": fear_count,
        "surprise":surprise_count,
        "anger": anger_count,
        "sadness": sadness_count,
        "disgust": disgust_count
        
    }

    sum_statistics(statistics)
    
    return statistics

#감정을 분류하여 json파일로 저장.
def main_analyze(video):
    with open(f"data/comments_{video['video_id']}.json", "r", encoding="utf-8") as f:
        egs = json.load(f)
    video_id=video['video_id']

    results = []
    for eg in egs[video_id]:
        result = inference(eg)
        results.append({"comment": eg, "emotion": result})

    # JSON파일에 감정 분류 결과를 저장한다
    output_file_path = f"data/analyzed_comments_{video['video_id']}.json"
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    # 메모리 해제 코드 추가
    gc.collect()
    torch.cuda.empty_cache()

    # 분류된 감정을 통계낸 후 RETURN한다
    return generate_statistics(video)


def sum_statistics(statistics):
    # 파일 경로 정의
    sum_statistics_file = "data/sum_comments_statistics.json"

    # 누적 통계를 담을 딕셔너리 초기화
    if os.path.exists(sum_statistics_file):
        # 기존 파일이 존재하면 파일에서 통계를 불러옴
        with open(sum_statistics_file, "r", encoding="utf-8") as f:
            sum_statistics_data = json.load(f)
    else:
        # 파일이 없을 경우 초기화된 딕셔너리 생성
        sum_statistics_data = {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "fear": 0,
            "surprise": 0,
            "anger": 0,
            "sadness": 0,
            "disgust": 0
        }

    # 현재 통계를 누적 통계에 더함
    for key in statistics:
        if key in sum_statistics_data:
            sum_statistics_data[key] += statistics[key]

    # 합산된 통계를 파일에 저장
    with open(sum_statistics_file, "w", encoding="utf-8") as f:
        json.dump(sum_statistics_data, f, ensure_ascii=False, indent=4)




