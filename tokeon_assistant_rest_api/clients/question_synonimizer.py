# app/clients/question_synonimizer.py

import inspect
from collections import namedtuple
import logging
from os.path import abspath

from tokeon_assistant_rest_api.clients.ModelNotFoundError import ModelNotFoundError

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
from pymorphy2 import MorphAnalyzer
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

# Синонимизация вопроса
def synonimize_question(question, model):
    question_tokens = preprocess(question)
    synonymized_question = []
    for word in question_tokens:
        if word in model.wv:
            synonyms = model.wv.most_similar(word, topn=2)
            synonymized_question.append((word, synonyms))
        else:
            synonymized_question.append((word, []))
    return synonymized_question


def result_question(question):
    questions = []
    logger.info(f"Searching model at path: {abspath(model_path)}")
    if not os.path.exists(model_path):
        logger.error("model does not exist")
        raise ModelNotFoundError(
            "FastText model and context are missing. "
            "Please run initial ingestion to build the knowledge base context and train the model."
        )

    model = FastText.load(model_path)

    synonyms = synonimize_question(question, model)
    synonymized_question = []
    for word, word_synonyms in synonyms:
        synonymized_question.append(word)  # Добавляем исходное слово
        if word_synonyms:  # Если есть синонимы
            # Добавляем первые 2 синонима из word_synonyms, можно сократить до 1
            synonymized_question.extend([syn[0] for syn in word_synonyms[:2]])
    synonymized_question = list(set(synonymized_question))
    synonymized_question = " ".join(synonymized_question)
    questions.append(question + " " + synonymized_question)
    return synonymized_question

