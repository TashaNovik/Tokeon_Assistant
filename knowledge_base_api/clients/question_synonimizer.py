# app/clients/question_synonimizer.py

import inspect
from collections import namedtuple
import logging
from os.path import abspath

logger = logging.getLogger(__name__)

# Monkey-patch for pymorphy2 compatibility on Python >=3.11
# Provide getargspec signature that matches argparse
ArgSpec = namedtuple('ArgSpec', 'args varargs varkw defaults')
def getargspec(func):
    spec = inspect.getfullargspec(func)
    return ArgSpec(args=spec.args, varargs=spec.varargs, varkw=spec.varkw, defaults=spec.defaults)
inspect.getargspec = getargspec

import re
import os
import nltk
import json
from pymorphy2 import MorphAnalyzer
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from gensim.models import FastText
from nltk.data import find

model_dir = os.getenv("FASTTEXT_MODEL_DIR",
                      os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fasttext")))
model_path = os.path.join(model_dir, "fasttext.model")

# Лемматизация текста
def lemmatize_ru(text):
    morph = MorphAnalyzer()
    words = re.findall(r'\b\w+\b', text.lower())
    lemmas = [morph.parse(word)[0].normal_form for word in words]
    return lemmas

# Предобработка текста
def preprocess(sentence):
    current_dir = os.path.dirname(__file__)
    nltk_dir = os.path.join(current_dir, "nltk")
    os.makedirs(nltk_dir, exist_ok=True)
    nltk.data.path.append(nltk_dir)

    # Инициализация stopwords один раз
    try:
        find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', download_dir=nltk_dir)
    stop_words = set(stopwords.words('russian'))

    words = lemmatize_ru(sentence)
    filtered_words = [word for word in words if word.isalpha() and word not in stop_words]
    return filtered_words


# Обучение модели FastText
def learning_model(processed_sentences):
    logger.info("Learning model... by sentences: " + str(len(processed_sentences)))
    os.makedirs(model_dir, exist_ok=True)
    model = FastText(
        vector_size=200,
        window=5,
        min_count=1,
        workers=4
    )
    model.build_vocab(processed_sentences)
    model.train(processed_sentences, total_examples=len(processed_sentences), epochs=10)
    model.save(model_path)


def learning_synonims(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    sentences = sent_tokenize(text, language='russian')
    processed_sentences = [preprocess(sentence) for sentence in sentences]
    return processed_sentences


