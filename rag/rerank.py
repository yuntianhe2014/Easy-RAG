import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained('E:\\model\\bge-reranker-large')
model = AutoModelForSequenceClassification.from_pretrained('E:\\model\\bge-reranker-large')
model.eval()


def rerank_topn(question,docs,N=5):
    pairs = []
    for i in docs:
        pairs.append([question,i.page_content])

    with torch.no_grad():
        inputs = tokenizer(pairs, padding=True, truncation=True, return_tensors='pt', max_length=512)
        scores = model(**inputs, return_dict=True).logits.view(-1, ).float()
    scores = scores.argsort().numpy()[::-1][:N]
    bk = []
    for i in scores:
        bk.append(docs[i])
    return bk