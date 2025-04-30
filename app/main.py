import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from telegram.ext import Application

from app.api.router.webhook import router as telegram_router
from app.api.router.telegram import create_bot

logger = logging.getLogger("app")

def configure_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage the application lifecycle:
      - Start the Telegram bot in polling mode on startup
      - Stop the Telegram bot cleanly on shutdown
    """
    logger.info("Starting Telegram bot in polling mode...")
    bot: Application = create_bot()
    await bot.initialize()
    await bot.start()
    await bot.bot.delete_webhook()
    # Commands are set in create_bot() via post_init
    asyncio.create_task(bot.updater.start_polling())
    app.state.bot = bot
    logger.info("Telegram bot started")

    yield  # Application is now ready to serve requests

    logger.info("Stopping Telegram bot polling...")
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    logger.info("Telegram bot stopped")


def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI app."""
    configure_logging()

    app = FastAPI(
        title="KnowledgeBaseGPT Bot",
        description="Telegram bot for answering user questions from a knowledge base using GPT",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        """Health check endpoint."""
        return {"status": "ok"}

    app.include_router(telegram_router)

    return app


app = create_app()

# async def async_process_file(file, dir):

#     loop = asyncio.get_event_loop()

#     # синхронная часть в отдельном потоке
#     physical_cores = cpu_count(logical=False)
#     max_workers = physical_cores
#     # количество физических ядер
#     with ProcessPoolExecutor(max_workers=max_workers) as pool:
#         filechunks = await loop.run_in_executor(
#             pool,
#             chunking,
#             dir,
#             file
#         )

#     # Асинхронная отправка
#     await async_send(filechunks, file, rewrite=True)
#     print(f"Запись {file} завершена")


# async def main(question=None, base_directory=None):
#     # monitor_task = asyncio.create_task(monitor())
#     if base_directory is not None:
#         txt_files = knowledge_base_runner(base_directory)
#         # Увеличиваем лимит одновременных задач, ограничиваем параллельные файлы (max_workers*sem)
#         sem = asyncio.Semaphore(1)

#         async def limited_process(file, dir):
#             async with sem:
#                 await async_process_file(file, dir)

#         tasks = [limited_process(file, dir)
#                  for file, dir in txt_files.items()]
#         await asyncio.gather(*tasks)

#     # создание токенизированного контекста для синонимизации, если не существует
#     # Надо делать первый раз, а потом вызывать при необходимости - временное решение с JSON, надо оптимизировать на БД (SQL и тд)
#     if base_directory == None:
#         with open("/context/context.json", 'r', encoding='utf-8') as f:
#             full_context = json.load(f)
#     else:
#         full_context = context("knowledge_base")

#     # переобучили модель на полном контексте
#     if base_directory != None:
#         learning_model(full_context)

#     if question is not None:

#         lemma_task = asyncio.to_thread(lemmatize_ru, question)
#         iam_token_task = asyncio.to_thread(get_token())

#         question_lemma, iam_token = await asyncio.gather(
#             lemma_task,
#             iam_token_task
#         )

#         question_top = await asyncio.to_thread(result_question, " ".join(question_lemma))

#         search_task = question_preparation(question_top)
#         answer_task = asyncio.to_thread(
#             send_request_to_yagpt,
#             iam_token,
#             await search_task,
#             system_prompt=f"Найди в тексте точный ответ на вопрос '{question}' и напиши краткий ответ. Если ответа нет - верни None",
#             temperature=0.0, #более строгий ответ в привязке к тексту
#             max_tokens=2000,
#             folder_id="b1glp0iqac5h7ihhmh7b"
#         )

#         answer = await answer_task
#         print(answer)
      
#     await asyncio.sleep(1)
#     # monitor_task.cancel()


# if __name__ == "__main__":
#     start_time = time.time()
#     # question = "Что такое криптоключ и из чего он состоит?"
#     # question = "как войти в систему?"
#     question = "как осуществляется выпуск ЦФА?"

#     # asyncio.run(main(question))
#     asyncio.run(main(question, base_directory="knowledge_base"))
#     dif_time = time.time() - start_time
#     print(f"Работа: {dif_time:.3f} секунд")
