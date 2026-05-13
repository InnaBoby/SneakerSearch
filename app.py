import os
import torch
import clip
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends
from qdrant_client import QdrantClient
import io
from PIL import Image
import torchvision.models as models
import logging

from utils import sneakers_classifier, get_clip_embedding

logger = logging.getLogger("uvicorn.error")

# #local_mode
# from dotenv import load_dotenv
# load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 6333)
MOBILENET_WEIGHTS = os.getenv("MOBILENET_WEIGHTS")
COLLECTION_NAME=os.getenv("COLLECTION_NAME")

device = "cuda" if torch.cuda.is_available() else "cpu"

# загрузка препроцессора и модели CLIP для получения эмбеддингов изображения
model, preprocessor = clip.load("ViT-B/32", device=device)

mobilenet = models.mobilenet_v3_large(weights="IMAGENET1K_V2")
num_features = mobilenet.classifier[3].in_features
mobilenet.classifier[3] = torch.nn.Linear(num_features, 2) 
state_dict = torch.load(MOBILENET_WEIGHTS)
mobilenet.load_state_dict(state_dict)
mobilenet.to(device)

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

    sneakers_proba = sneakers_classifier(image, mobilenet, device)
    logger.info(f"Загруженное фото содержит кроссовки с вероятностью {sneakers_proba}")
    if sneakers_proba < 0.5:
        return {"results": f"Нa фото нет кроссовка с вероятностью {1-sneakers_proba}"}

    image_emb = get_clip_embedding(image, preprocessor, model, device)

    candidates = client.query_points(
                                    collection_name=COLLECTION_NAME,
                                    query=image_emb, 
                                    using="photos",
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
