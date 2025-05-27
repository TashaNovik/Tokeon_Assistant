import logging
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Body
from pydantic import BaseModel
from knowledge_base_api.clients.ModelNotFoundError import ModelNotFoundError
from knowledge_base_api.clients.question_processor import process_question
from knowledge_base_api.clients.renew_base import main as renew_knowledge_base
import zipfile
import tempfile

logger = logging.getLogger(__name__)
knowledge_base_router = APIRouter()

class QuestionRequest(BaseModel):
    question: str

@knowledge_base_router.post(
    "/knowledge-base/renew",
    status_code=status.HTTP_200_OK,
    summary="Обновить базу знаний",
    description="Запускает процесс обновления базы знаний в векторной базе."
)
async def update_knowledge_base(zip_file: UploadFile = File(...)):
    """
    Updates the knowledge base from the uploaded ZIP file.

    Args:
        zip_file (UploadFile): ZIP file containing data to update the knowledge base.

    Returns:
        dict: Message indicating successful knowledge base update.

    Raises:
        HTTPException: If an error occurs during the update, returns a 500 error with details.
    """
    try:
        logger.info(f"Renew knowledge base by zip_file: {zip_file}")

        temp_file_path = f"/tmp/{zip_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await zip_file.read())

        logger.info(f"Received zip_file: {zip_file}, saved to {temp_file_path}")

        data_folder = tempfile.mkdtemp()
        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            logger.info(f"Extracting zip_file to {data_folder}")
            zip_ref.extractall(data_folder)

        await renew_knowledge_base(data_folder)
        return {"message": "База знаний успешно обновлена."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@knowledge_base_router.post(
    "/knowledge-base/prepare-question",
    status_code=status.HTTP_200_OK,
    summary="Подготовить данные из базы знаний для вопроса",
    description="Получает и обрабатывает данные из базы знаний на основе вопроса пользователя."
)
async def prepare_question(request: QuestionRequest):
    """
    Endpoint to prepare relevant knowledge base data for a question.
    """
    try:
        logger.info(f"Preparing knowledge base data for question: {request.question}")

        result_text = await process_question(request.question)

        logger.info(f"Prepared knowledge base data: {result_text[:100]}...")

        return {"data": result_text}

    except ModelNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="База знаний обновляется, пожалуйста подождите."
        )
            
    except Exception as e:
        logger.error(f"Error preparing knowledge base data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
