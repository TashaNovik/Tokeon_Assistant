import asyncio
import json
import time
from concurrent.futures import ProcessPoolExecutor

from psutil import cpu_count

from app.clients.chunking import chunking, knowledge_base_runner
from app.clients.qdrant_sender import async_send

async def _process_file(file_path, directory):
    loop = asyncio.get_event_loop()
    cores = cpu_count(logical=False)
    with ProcessPoolExecutor(max_workers=cores) as pool:
        chunks = await loop.run_in_executor(pool, chunking, directory, file_path)
    await async_send(chunks, file_path, rewrite=True)
    print(f"Finished {file_path}")

async def main(base_dir: str):
    txt_files = knowledge_base_runner(base_dir)
    sem = asyncio.Semaphore(1)

    async def limited(f, d):
        async with sem:
            await _process_file(f, d)

    await asyncio.gather(*(limited(f, d) for f, d in txt_files.items()))

if __name__ == "__main__":
    start = time.time()
    asyncio.run(main("knowledge_base"))
    print("Done in", time.time() - start)
