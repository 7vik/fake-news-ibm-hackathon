#!/usr/bin/env python

import numpy as np
import sys
import os
import nltk
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
# import keras
import json
# from keras.models import Sequential
# from keras.layers import Dense, GRU,LSTM, Dropout, Bidirectional, Embedding
# from keras.callbacks import LambdaCallback, ModelCheckpoint, EarlyStopping

BASE_URL_1 = "../teamName/training/celebrityDataset/"
BASE_URL_2 = "../teamName/training/fakeNewsDataset/"
PATH1 = "../ibm-api-connect/natlang_responses/celebrityDataset/"
PATH2 = "../ibm-api-connect/tone_responses/celebrityDataset/"
PATH21 = "../ibm-api-connect/natlang_responses/fakeNewsDataset/"
PATH22 = "../ibm-api-connect/tone_responses/fakeNewsDataset/"

print("loading data...")
print("loading file embeddings...")
f = open('glove.6B.100d.txt')
embeddings_index = dict()
for line in f:
	values = line.split()
	word = values[0]
	coefs = np.asarray(values[1:], dtype='float32')
	embeddings_index[word] = coefs
f.close()
print("loaded {} file embeddings".format(len(embeddings_index.keys())))
def load_fromdir(BASE_URL, PATH_TO_API, PATH2):
    file_list = os.listdir(BASE_URL)
    res_list = []
    sentiment_list = []
    concept_list = []
    keywords_list = []
    tone_list = []
    for fileid in file_list:
        file_name = "".join(fileid.split(".")[:-1])+".json"
        api_file = open(PATH_TO_API+file_name)
        api_json = json.load(api_file)
        sentiment = api_json["sentiment"]["document"]["score"]
        concepts = [(concepts["text"], concepts["relevance"]) for concepts in api_json["concepts"]]
        categories  = (api_json["categories"][0]["label"].split("/"),api_json["categories"][0]["score"])
        keywords = [(keywords["text"],keywords["relevance"]) for keywords in api_json["keywords"]]
        api_file.close()
        api_file = open(PATH2+file_name)
        api_json = json.load(api_file)
        tones = [(tone["tone_id"],tone["score"]) for tone in api_json["document_tone"]["tones"]]
        api_file.close
        opened = open(BASE_URL+fileid)
        text = opened.read()
        res_list.append(text)
        sentiment_list.append(sentiment)
        concept_list.append(concepts)
        tone_list.append(tones)
        keywords_list.append(keywords)
        opened.close()
    print(len(res_list))
    return res_list, concept_list, sentiment_list, tone_list, keywords_list

fake_list,fake_concept_list, fake_sentiment_list, fake_tone_list, fake_keywords_list = load_fromdir(BASE_URL_1+"fake/",PATH1+"fake/", PATH2+"fake/")
real_list,real_concept_list, real_sentiment_list, real_tone_list, real_keywords_list = load_fromdir(BASE_URL_1+"legit/",PATH1+"legit/", PATH2+"legit/")
fake_list2,fake_concept_list2, fake_sentiment_list2, fake_tone_list2, fake_keywords_list2 = load_fromdir(BASE_URL_2+"fake/",PATH21+"fake/", PATH22+"fake/")
real_list2,real_concept_list2, real_sentiment_list2, real_tone_list2, real_keywords_list2 = load_fromdir(BASE_URL_2+"legit/",PATH21+"legit/", PATH22+"legit/")

fake_list.extend(fake_list2)
fake_concept_list.extend(fake_concept_list2)
fake_sentiment_list.extend(fake_sentiment_list2)
fake_tone_list.extend(fake_tone_list2)
fake_keywords_list.extend(fake_keywords_list2)

real_list.extend(real_list2)
real_concept_list.extend(real_concept_list2)
real_sentiment_list.extend(real_sentiment_list2)
real_tone_list.extend(real_tone_list2)
real_keywords_list.extend(real_keywords_list2)

print("loaded!")
total = real_list+fake_list
total_concept = real_concept_list+fake_concept_list
total_tone = real_tone_list+fake_tone_list
total_sentiment = real_sentiment_list+fake_sentiment_list
total_keywords = real_keywords_list+fake_keywords_list

targets = [1 for i in real_list]+[0 for i in fake_list]
print("preprocessing")
def boolean_indexing(v, fillval=0.0):
    lens = np.array([len(item) for item in v])
    mask = lens[:,None] > np.arange(lens.max())
    out = np.full(mask.shape,fillval)
    out[mask] = np.concatenate(v)
    return out

total_as_vectors = []
total_relevance = []
for i in range(len(total)):
    my_embeddings = np.ndarray((100))
    total_relevance.append([keyword[1] for keyword in total_keywords[i]])
    my_concepts = np.ndarray((100))
    for concept_list in total_concept[i]:
        temp_concept = np.zeros((100))
        for concept in nltk.word_tokenize(concept_list[0])[-1:]:
            temp_concept +=embeddings_index.get(concept.lower(), np.zeros((100)))
        my_concepts+=temp_concept*concept_list[1]
    my_tones = np.ndarray((100))
    for tone in total_tone[i]:
        my_tones+=embeddings_index.get(tone[0],np.zeros((100)))*tone[1]
    tokenized = nltk.word_tokenize(total[i])
    for j in tokenized:
        try:
            my_embeddings+=embeddings_index[j.lower()]
        except:
            #print("Missed a word")
            #print(j)
            continue

    total_as_vectors.append(np.concatenate((my_embeddings,my_tones,np.array(total_sentiment[i]),my_concepts), axis=None))

total_relevance = boolean_indexing(total_relevance)
total = np.concatenate((total_as_vectors,total_relevance), axis=1)
print("loading model")

# model = Sequential()
# model.add(Embedding(vocab_size, 100,weights=[embedding_matrix], trainable=False))
# model.add(Bidirectional(LSTM(64,stateful=False)))
# model.add(Dropout(0.4))
# #model.add(Dense(32,activation="relu",))# kernel_regularizer=keras.regularizers.l2(0.01),
#                # activity_regularizer=keras.regularizers.l1(0.01)))
# #model.add(Dropout(0.4))
# model.add(Dense(1,activation="sigmoid"))
# model.compile(loss='binary_crossentropy', optimizer="adam", metrics=['accuracy'])
# model.summary()

# model.load_weights()
X_train, X_test, y_train, y_test = train_test_split(total_as_vectors, targets, random_state=0)
logreg = LogisticRegression()
logreg.fit(X_train, y_train)

print("Train accuracy {}".format(logreg.score(X_train,y_train)))
print("Test accuracy {}".format(logreg.score(X_test,y_test)))