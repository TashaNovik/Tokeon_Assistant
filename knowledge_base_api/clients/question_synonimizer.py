import inspect
from collections import namedtuple
import logging
from os.path import abspath

from knowledge_base_api.clients.ModelNotFoundError import ModelNotFoundError

logger = logging.getLogger(__name__)

# Monkey-patch for pymorphy2 compatibility on Python >=3.11
# Provide getargspec signature that matches argparse
ArgSpec = namedtuple('ArgSpec', 'args varargs varkw defaults')


def getargspec(func):
    """
    Compatibility patch for pymorphy2 on Python 3.11+, replaces inspect.getargspec.

    Args:
        func (callable): Function to analyze.

    Returns:
        ArgSpec: Named tuple with function arguments.
    """
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

def lemmatize_ru(text):
    """
    Lemmatizes Russian text and returns a list of normalized words.

    Args:
        text (str): Input text.

    Returns:
        list[str]: List of lemmas (normalized word forms).
    """
    morph = MorphAnalyzer()
    words = re.findall(r'\b\w+\b', text.lower())
    lemmas = [morph.parse(word)[0].normal_form for word in words]
    return lemmas


def preprocess(sentence):
    """
    Preprocesses a sentence: lemmatization, stop-word and non-alphabetic token filtering.

    Args:
        sentence (str): Input sentence.

    Returns:
        list[str]: List of cleaned and lemmatized words.
    """
    current_dir = os.path.dirname(__file__)
    nltk_dir = os.path.join(current_dir, "nltk")
    os.makedirs(nltk_dir, exist_ok=True)
    nltk.data.path.append(nltk_dir)


    try:
        find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', download_dir=nltk_dir)
    stop_words = set(stopwords.words('russian'))

    words = lemmatize_ru(sentence)
    filtered_words = [word for word in words if word.isalpha() and word not in stop_words]
    return filtered_words


def learning_model(processed_sentences):
    """
    Trains a FastText model on the processed sentences and saves it.

    Args:
        processed_sentences (list[list[str]]): List of sentences where each is a list of tokens.
    """
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
    """
    Reads text from a file, splits it into sentences, and preprocesses them.

    Args:
        file_path (str): Path to the text file.

    Returns:
        list[list[str]]: List of preprocessed sentences with tokens.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    sentences = sent_tokenize(text, language='russian')
    processed_sentences = [preprocess(sentence) for sentence in sentences]
    return processed_sentences



# Синонимизация вопроса

def synonimize_question(question, model):
    """
    Retrieves synonyms for each word in the question using a trained FastText model.

    Args:
        question (str): Input question.
        model (FastText): Trained FastText model.

    Returns:
        list[tuple(str, list)]: List of tuples (word, list of similar words with scores).
    """
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
    """
    Constructs an expanded question with synonyms, training the model if needed.

    Args:
        question (str): Input question.

    Returns:
        str: String with the original question and added synonyms.

    Raises:
        RuntimeError: If the model and context are missing.
    """
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
        synonymized_question.append(word)
        if word_synonyms:
            synonymized_question.extend([syn[0] for syn in word_synonyms[:2]])
    synonymized_question = list(set(synonymized_question))
    synonymized_question = " ".join(synonymized_question)
    questions.append(question + " " + synonymized_question)
    return synonymized_question

def context(base_directory):
    """
    Loads or creates context from knowledge base files and saves to context.json.

    Args:
        base_directory (str or None): Path to the knowledge base. If None, loads from context.json.

    Returns:
        list: List of tokenized sentences for the entire context.
    """
    logger.info(f"Searching context files in the base directory: {base_directory}")
    context_dir = os.path.join(os.getcwd(), "context")
    logger.info(f"Searching context files in the context dir: {context_dir}")
    os.makedirs(context_dir, exist_ok=True)

    context_file = os.path.join(context_dir, "context.json")
    logger.info(f"Searching context file in: {context_file}")

    if base_directory == None and os.path.exists(context_file):
        logger.info(f"base_directory is None and context file exists at {context_file}")
        with open(context_file, 'r', encoding='utf-8') as f:
            full_context = json.load(f)
    else:
        logger.info("Searching context files in the directory: knowledge_base")
        context_files = knowledge_base_runner("knowledge_base")
        full_context = []
        for file, directory in context_files.items():
            print("Идет запись из файла: ", file)
            context = learning_synonims(directory)
            full_context += context
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(full_context, f, ensure_ascii=False, indent=2)

    return full_context
