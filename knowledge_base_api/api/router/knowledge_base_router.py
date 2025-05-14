import logging
from fastapi import APIRouter, HTTPException, status, UploadFile, File

from knowledge_base_api.clients.renew_base import main as renew_knowledge_base
import zipfile
import tempfile

logger = logging.getLogger(__name__)
knowledge_base_router = APIRouter()

@knowledge_base_router.post(
    "/knowledge-base/renew",
    status_code=status.HTTP_200_OK,
    summary="Обновить базу знаний",
    description="Запускает процесс обновления базы знаний в векторной базе."
)
async def update_knowledge_base(zip_file: UploadFile = File(...)):
    """
    Эндпоинт для обновления базы знаний.
    """
    try:

        logger.info(f"Renew knowledge base by zip_file: {zip_file}")

        # Save the uploaded file to a temporary location
        temp_file_path = f"/tmp/{zip_file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await zip_file.read())

        logger.info(f"Received zip_file: {zip_file}, saved to {temp_file_path}")

        data_folder = tempfile.mkdtemp()
        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            logger.info(f"Extracting zip_file to {data_folder}")
            zip_ref.extractall(data_folder)

        await renew_knowledge_base(data_folder)  # Вызов функции main для обновления базы знаний
        return {"message": "База знаний успешно обновлена."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
