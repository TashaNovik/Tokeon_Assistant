import asyncio
import json
import time
from concurrent.futures import ProcessPoolExecutor

from psutil import cpu_count

from knowledge_base_api.clients.chunking import chunking, knowledge_base_runner
from knowledge_base_api.clients.qdrant_sender import async_send
import logging
logger = logging.getLogger(__name__)

async def _process_file(file_path, directory):
    loop = asyncio.get_event_loop()
    cores = cpu_count(logical=False)
    with ProcessPoolExecutor(max_workers=cores) as pool:
        print(f"Process file path: {file_path}. Directory: {directory}")
        chunks = await loop.run_in_executor(pool, chunking, directory, file_path)
    await async_send(chunks, file_path, rewrite=True)
    print(f"Finished {file_path}")

async def main(base_dir: str):
    logger.info(f"Process directory: {base_dir}")
    txt_files = knowledge_base_runner(base_dir)
    logger.info(f"Found {len(txt_files)} files to process in {base_dir}")
    sem = asyncio.Semaphore(1)

    async def limited(f, d):
        async with sem:
            await _process_file(f, d)

    await asyncio.gather(*(limited(f, d) for f, d in txt_files.items()))

if __name__ == "__main__":
    start = time.time()
    asyncio.run(main("knowledge_base"))
    print("Done in", time.time() - start)
