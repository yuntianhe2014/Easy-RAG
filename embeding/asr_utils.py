#coding:utf-8
from funasr import AutoModel
# paraformer-zh is a multi-functional asr model
# use vad, punc, spk or not as you need
model = AutoModel(model="paraformer-zh",  vad_model="fsmn-vad", punc_model="ct-punc",
                  # spk_model="cam++"
                  )
def get_spk_txt(file):
    res = model.generate(input=file,
                batch_size_s=300,
                hotword='魔搭')
    print(res[0]["text"])
    fw = "embeding/tmp.txt"
    f = open(fw,"w",encoding="utf-8")
    f.write('"context"\n'+res[0]["text"])
    f.close()
    return fw