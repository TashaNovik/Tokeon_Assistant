import asyncio
import os
import json
from functools import partial
from knowledge_base_api.clients.chunking import knowledge_base_runner, chunking
from knowledge_base_api.clients.qdrant_sender import async_send
from knowledge_base_api.clients.question_synonimizer import learning_synonims

import logging
logger = logging.getLogger(__name__)

async def main(kb_dir=None):
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
    context(kb_dir)


def context(kb_dir):
    context_dir = os.path.join(os.path.dirname(__file__),
                               "..", "..", "context")
    context_dir = os.path.abspath(context_dir)
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


if __name__ == "__main__":
    asyncio.run(main())
