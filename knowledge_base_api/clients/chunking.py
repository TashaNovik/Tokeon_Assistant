import os
from functools import lru_cache
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct

import logging
logger = logging.getLogger(__name__)

@lru_cache(maxsize=None)
def get_model():
    """
    Load and cache the SentenceTransformer model for multilingual embeddings.

    Returns:
        SentenceTransformer: Initialized SentenceTransformer model.
    """
    return SentenceTransformer("intfloat/multilingual-e5-large")


def chunking(input_file, name):
    """
    Splits a text file into large and small chunks,
    computes their embeddings, and creates point lists for indexing.

    Args:
        input_file (str): Path to the text file to be processed.
        name (str): Document name (used in the payload of points).

    Returns:
        dict: Dictionary with two lists of points:
            {
                "Large": list of PointStruct for large chunks,
                "Small": list of PointStruct for small chunks
            }
        Returns None if the file is not found.
    """
    logger.info(f"chunking {input_file}")
    small_chunk_size = 300
    small_chunk_overlap = 80
    large_chunk_size = 2500
    large_chunk_overlap = 400


    large_splitter = RecursiveCharacterTextSplitter(
        chunk_size=large_chunk_size,
        chunk_overlap=large_chunk_overlap,
        separators=['\n\nГлава ', '\n\nРаздел ', '\n\nСтатья ', '\nПункт ', '\n\n', '\n'])


    small_splitter = RecursiveCharacterTextSplitter(
        chunk_size=small_chunk_size,
        chunk_overlap=small_chunk_overlap,
        separators=['\n\nГлава ', '\n\nРаздел ', '\n\nСтатья ', '\nПункт ', '\n\n', '\n'])

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден!")
        return


    large_chunks = large_splitter.split_text(text)

    points_small = []
    points_large = []
    model = get_model()
    i = 0
    for large_id, large_chunk in enumerate(large_chunks):
        if len(large_chunk) < small_chunk_size * 2:
            small_chunks = [large_chunk]
        else:
            small_chunks = small_splitter.split_text(large_chunk)

        large_embedding = model.encode(large_chunk).tolist()

        points_large.append(PointStruct(
            id=i,
            vector=large_embedding,
            payload={
                "document_name": name,
                "text": large_chunk,
                "parent_id": i
            }
        ))
        large_id = i
        i += 1

        for small_chunk in small_chunks:
            small_embedding = model.encode(small_chunk).tolist()
            points_small.append(PointStruct(
                id=i,
                vector=small_embedding,
                payload={
                    "document_name": name,
                    "text": None,
                    "parent_id": large_id
                }
            ))
            i += 1
    logger.info(f"chunking {input_file} done")
    return {"Large": points_large, "Small": points_small}


def knowledge_base_runner(directory):
    """
    Scans the specified directory (or file) and returns a dictionary of
    text file names (without extension) and their full paths.

    Args:
        directory (str): Relative path to a directory or a file.

    Returns:
        dict: Dictionary where the key is the filename without .txt,
              and the value is the full file path.
              If a .txt file is passed, returns a dictionary with one element.
    """
    txt_files = {}
    base_dir = os.path.join(os.path.dirname(__file__), directory)

    logger.info("knowledge_base_runner: Base directory: " + base_dir)
    if base_dir.endswith(".txt"):
        return {directory[:-4]: base_dir}
    else:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".txt"):
                    txt_files.update({file[:-4]: (os.path.join(root, file))})

    logger.info(f"knowledge_base_runner: Found {len(txt_files)} files in {base_dir}")
    return txt_files


