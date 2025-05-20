import asyncio
import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from itertools import islice


def batched(iterable, batch_size):
    """
    Splits an iterable into chunks (batches) of a specified size.

    Args:
        iterable (iterable): Input iterable.
        batch_size (int): Size of each batch.

    Yields:
        list: Next batch of elements from the iterable.
    """
    iterator = iter(iterable)
    while batch := list(islice(iterator, batch_size)):
        yield batch


async def async_send(filechunks, filename, rewrite=False):
    """
    Asynchronously sends embeddings from chunks to a Qdrant collection.

    If a collection with the given name already exists, it will either be deleted and recreated,
    or skipped depending on the `rewrite` flag.

    Args:
        filechunks (dict): Dictionary with "Large" and "Small" keys containing lists of points (PointStruct or dict).
        filename (str): Name of the Qdrant collection to store the data.
        rewrite (bool, optional): If True, deletes the existing collection before loading data. Defaults to False.

    Raises:
        Exception: Propagates exceptions encountered during interaction with Qdrant.
    """
    client = AsyncQdrantClient(
        host=os.getenv("QDRANT_HOST", "qdrant"),  # <— сейчас docker-dns имя
        port=int(os.getenv("QDRANT_PORT", 6333)),
        prefer_grpc=True,
        timeout=120
    )

    size = 1024
    collection_name = filename

    try:
        existing_collections = await client.get_collections()
        exists = any(col.name == collection_name for col in existing_collections.collections)

        if exists:
            if rewrite:
                await client.delete_collection(collection_name)
            else:
                print(f"Collection {collection_name} exists. passing")
                return

        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=size, distance=Distance.DOT)
        )

        async def upsert_batch(points):
            converted = [
                PointStruct(**p) if isinstance(p, dict) else p
                for p in points
            ]
            await client.upsert(
                collection_name=collection_name,
                points=converted,
                wait=False
            )

        tasks = []
        for batch in batched(filechunks["Large"], 200):
            tasks.append(upsert_batch(batch))

        for batch in batched(filechunks["Small"], 500):
            tasks.append(upsert_batch(batch))

        await asyncio.gather(*tasks)

    except Exception as e:
        print(f"Error processing {collection_name}: {str(e)}")
    finally:
        await client.close()
