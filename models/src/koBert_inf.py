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


## infer setup
device = torch.device("cuda:0")
tokenizer = KoBERTTokenizer.from_pretrained('skt/kobert-base-v1')
bertmodel = BertModel.from_pretrained('skt/kobert-base-v1', return_dict=False)
vocab = nlp.vocab.BERTVocab.from_sentencepiece(tokenizer.vocab_file, padding_token='[PAD]')
tok = nlp.data.BERTSPTokenizer(tokenizer, vocab, lower = False)
max_len = 64
batch_size = 64
tok = tokenizer.tokenize

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
                 hidden_size = 768,
                 num_classes = 7,
                 dr_rate = None,
                 params = None):
        super(BERTClassifier, self).__init__()
        self.bert = bert
        self.dr_rate = dr_rate

        self.classifier = nn.Linear(hidden_size , num_classes)
        if dr_rate:
            self.dropout = nn.Dropout(p = dr_rate)

    def gen_attention_mask(self, token_ids, valid_length):
        attention_mask = torch.zeros_like(token_ids)
        for i, v in enumerate(valid_length):
            attention_mask[i][:v] = 1
        return attention_mask.float()

    def forward(self, token_ids, valid_length, segment_ids):
        attention_mask = self.gen_attention_mask(token_ids, valid_length)

        _, pooler = self.bert(input_ids = token_ids, token_type_ids = segment_ids.long(), attention_mask = attention_mask.float().to(token_ids.device),return_dict = False)
        if self.dr_rate:
            out = self.dropout(pooler)
        return self.classifier(out)
    

# trained model weight load 
model = BERTClassifier(bertmodel, dr_rate = 0.5).to(device)
model.load_state_dict(torch.load('../weight/kobert241107.pth'))

def inference(predict_sentence): 

    data = [predict_sentence, '0']
    dataset_another = [data]

    another_test = BERTDataset(dataset_another, 0, 1, tok, vocab, max_len, True, False) # tokenized input senten..
    test_dataloader = torch.utils.data.DataLoader(another_test, batch_size = batch_size, num_workers = 5) # torch type
    
    model.eval() 
    test_eval = ""
    score = 0.00
    for batch_id, (token_ids, valid_length, segment_ids, label) in enumerate(test_dataloader):
        token_ids = token_ids.long().to(device)
        segment_ids = segment_ids.long().to(device)

        valid_length = valid_length
        label = label.long().to(device)

        out = model(token_ids, valid_length, segment_ids)

        for i in out: # out = model(token_ids, valid_length, segment_ids)
            logits = i
            logits = logits.detach().cpu().numpy()

            emotion = np.argmax(logits)

            if emotion <= 3 or emotion >= 6:
                test_evall = "부정"
            elif emotion == 5:  # 행복
                test_evall = "긍정"
            elif emotion == 4:  # 중립
                test_evall = "중립"

    return test_eval

if __name__ == "__main__":
    egs = ["시간이 갈수록 퍼거슨감독의 역량이 빛나보인다.", "민심을 무겁게 받아들인다는 문자 그대로의 뜻을 아니?", "역쉬 돈쓰는데는 아낌없는 한화~ㅋㅋㅋㅋ"]
    for eg in egs : 
        result = inference(eg) 
        print(result)