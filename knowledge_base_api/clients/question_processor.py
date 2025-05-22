import asyncio
from asyncio import to_thread
import os
from qdrant_client import AsyncQdrantClient
import logging

from knowledge_base_api.clients.chunking import get_model

logger = logging.getLogger(__name__)

from knowledge_base_api.clients.question_synonimizer import lemmatize_ru, result_question

model = get_model()

async def async_search(client, collection, question_embedding):
    return await client.search(
        collection_name=collection,
        query_vector=question_embedding,
        limit=10,
        score_threshold=0.25,
        with_payload=["parent_id"]
    )

async def question_preparation(question):
    client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),
        port=int(os.getenv("QDRANT_PORT", 6333)),
        prefer_grpc=True
    )
    try:
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        embedding = await to_thread(model.encode, question)
        question_embedding = embedding.tolist()

        tasks = [async_search(client, col, question_embedding)
                 for col in collection_names]
        results = await asyncio.gather(*tasks)

        top_chunks = []
        seen_ids = set()

        for col_name, col_results in zip(collection_names, results):
            for hit in col_results:
                pid = hit.payload["parent_id"]
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    top_chunks.append((hit.score, pid, col_name))

        top_chunks.sort(reverse=True, key=lambda x: x[0])
        top5 = top_chunks[:5]

        retrieve_tasks = [
            client.retrieve(
                collection_name=item[2],
                ids=[item[1]],
                with_payload=["text"]
            ) for item in top5
        ]
        texts = await asyncio.gather(*retrieve_tasks)
    finally:
        await client.close()

    return "\n".join([t[0].payload["text"] for t in texts])

async def process_question(raw_question):
    lemmas = await to_thread(lemmatize_ru, raw_question)
    logger.info(f"Question lemmas: {lemmas}")
    top_question = result_question(" ".join(lemmas))
    logger.info(f"Top question: {top_question}")
    question = await question_preparation(top_question)
    return question

