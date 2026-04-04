import os
import torch
import clip
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends
from qdrant_client import QdrantClient
import io
from PIL import Image

from utils import get_image_embedding

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 6333)

device = "cuda" if torch.cuda.is_available() else "cpu"

# загрузка препроцессора и модели CLIP для получения эмбеддингов изображения
model, preprocessor = clip.load("ViT-B/32", device=device)

@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    Функция для контроля за экземпляром клиента 
    '''
    # создаем клиента при запуске приложения
    app.state.qdrant_client = QdrantClient(DB_HOST, port=DB_PORT)
    print("Qdrant client connected")
    yield
    # закрываем соединение при остановке приложения
    app.state.qdrant_client.close()
    print("Qdrant client disconnected")

app = FastAPI(title="Search Similar Sneakers App", lifespan=lifespan)

def get_qdrant_client():
    '''
    Функция для получения клиента в эндпоинтах (Dependency)
    '''
    return app.state.qdrant_client

@app.post("/helthcheck")
async def helthcheck():
    '''
    Функция для хэлсчека приложения
    '''
    return "Service is available"

@app.post("/search")
async def serch_similar_sneakers(
    upload_image: UploadFile = File(),
    client: QdrantClient = Depends(get_qdrant_client)):
    '''
    Эндпоинт для поиска похожих изображений по загруженному фото
    '''

    request = await upload_image.read()
    image = Image.open(io.BytesIO(request)).convert("RGB")

    image_emb = get_image_embedding(image, preprocessor, model, device)

    candidates = client.query_points(
                                    collection_name="sneakers",
                                    query=image_emb, 
                                    limit=5,           
                                    with_payload=True   # Возвращаем бренд, модель и путь из CSV
                                ).points
    
    results = [
        {
            "id": candidate.id,
            "score": candidate.score,
            "brand": candidate.payload.get("brand"),
            "model": candidate.payload.get("model"),
            "image_url": candidate.payload.get("path_to_photo")
        }
        for candidate in candidates
    ]

    return {"results": results}
