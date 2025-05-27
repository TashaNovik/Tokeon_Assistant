import asyncio
import os
import json
from functools import partial
from knowledge_base_api.clients.chunking import knowledge_base_runner, chunking
from knowledge_base_api.clients.qdrant_sender import async_send
from knowledge_base_api.clients.question_synonimizer import learning_synonims, learning_model, model_path

import logging
logger = logging.getLogger(__name__)

async def main(kb_dir=None):
    """
    Main async entry point for processing the knowledge base:

    - Determines the knowledge‑base directory if not provided.
    - Scans and loads all knowledge‑base files.
    - Splits each file into chunks and uploads the data to Qdrant.
    - Refreshes the context by calling :func:`context` in a separate executor.

    Args:
        kb_dir (str | None): Path to the knowledge‑base directory.
            If *None*, the default ``knowledge_base`` directory is used.
    """
    if kb_dir is None:
        kb_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
    logger.info(f"Process kb_dir: {kb_dir}")
    files = knowledge_base_runner(kb_dir)
    for name, path in files.items():
        print(f"Загрузка в Qdrant «{name}» ")
        filechunks = chunking(path, name)
        await async_send(filechunks, name, rewrite=True)

    loop = asyncio.get_event_loop()

    await loop.run_in_executor(None, partial(context, kb_dir))
<<<<<<< HEAD

    context(kb_dir)
=======
>>>>>>> origin/main

    full_ctx = context(kb_dir)
    if not full_ctx:
        raise RuntimeError(
            "FastText model and context are missing. "
            "Please run initial ingestion to build the knowledge base context and train the model."
        )

    if os.path.exists(model_path):
        logger.info(f"Model already exists at {model_path}. Removing and retraining...")
        os.remove(model_path)

    learning_model(full_ctx)

def context(kb_dir):
<<<<<<< HEAD
    """
    Collects context from knowledge‑base files and stores it as JSON.

    Args:
        kb_dir (str): Path to the knowledge‑base directory.
    """
    context_dir = os.path.join(os.path.dirname(__file__),
                               "..", "..", "context")
    context_dir = os.path.abspath(context_dir)
=======
    context_dir = os.getenv("CONTEXT_DIR",
                            os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "..", "data", "context")))
>>>>>>> origin/main
    os.makedirs(context_dir, exist_ok=True)

    context_file = os.path.join(context_dir, "context.json")

    context_files = knowledge_base_runner(kb_dir)

    full_context = []
    for file, directory in context_files.items():
        print("Модель. Идет запись из файла: ", file)
        context = learning_synonims(directory)
        full_context += context
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(full_context, f, ensure_ascii=False, indent=2)
    return full_context

if __name__ == "__main__":
    asyncio.run(main())
