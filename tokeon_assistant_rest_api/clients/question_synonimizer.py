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
from tokeon_assistant_rest_api.clients.chunking import knowledge_base_runner


def lemmatize_ru(text):
    """Lemmatize Russian text into a list of normalized word forms.

        Args:
            text: Input Russian text.

        Returns:
            List of lemmatized words.
    """
    morph = MorphAnalyzer()
    words = re.findall(r'\b\w+\b', text.lower())
    lemmas = [morph.parse(word)[0].normal_form for word in words]
    return lemmas


def preprocess(sentence):
    """Preprocess a sentence by lemmatizing and removing stopwords and non-alphabetic tokens.

        Downloads necessary NLTK data if missing.

        Args:
            sentence: Input sentence text.

        Returns:
            List of processed tokens.
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
    """Train a FastText model on the given tokenized sentences and save it locally.

            Args:
                processed_sentences: List of tokenized and preprocessed sentences.
    """
    logger.info("Learning model... by sentences: " + str(len(processed_sentences)))
    os.makedirs("fasttext", exist_ok=True)
    model = FastText(
        vector_size=200,
        window=5,
        min_count=1,
        workers=4
    )
    model.build_vocab(processed_sentences)
    model.train(processed_sentences, total_examples=len(processed_sentences), epochs=10)
    model_path = os.path.join("fasttext", "fasttext.model")
    model.save(model_path)


def learning_synonims(file_path):
    """Read a text file, split into sentences, preprocess them for synonym model training.

        Args:
            file_path: Path to the text file.

        Returns:
            List of tokenized and preprocessed sentences.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    sentences = sent_tokenize(text, language='russian')
    processed_sentences = [preprocess(sentence) for sentence in sentences]
    return processed_sentences


def synonimize_question(question, model):
    """Generate synonyms for each token in the question using a FastText model.

    Args:
        question: Input question string.
        model: Trained FastText model.

    Returns:
        List of tuples of (word, list of synonyms with similarity scores).
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
    """Generate a synonym-augmented version of the question using the FastText model.

    Loads the FastText model, training it if missing, and returns
    the original question extended with the most similar synonyms.

    Args:
        question: Input question string.

    Raises:
        RuntimeError: If neither model nor context is available to build it.

    Returns:
        Synonym-augmented question string.
    """
    questions = []
    model_dir = "fasttext"
    model_path = os.path.join(model_dir, "fasttext.model")
    logger.info(f"Searching model at path: {abspath(model_path)}")
    if not os.path.exists(model_path):
        logger.error("model does not exist")
        full_ctx = context(None)
        if not full_ctx:
            raise RuntimeError(
                "FastText model and context are missing. "
                "Please run initial ingestion to build the knowledge base context and train the model."
            )

        logger.error("model does not exist. Learning model...")
        learning_model(full_ctx)

    logger.info(f"Loading model from path: {abspath(model_path)}")
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
    """Load or build the context from knowledge base files for training the FastText model.

    If a context JSON file exists and no base_directory is provided, loads from it.
    Otherwise, reads text files from the knowledge base directory, preprocesses,
    and saves the context to a JSON file.

    Args:
        base_directory: Directory containing knowledge base text files or None.

    Returns:
        List of preprocessed sentences representing the full context.
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

