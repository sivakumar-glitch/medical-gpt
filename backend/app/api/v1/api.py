from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, chat_history, stt, upload

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/rag", tags=["chat"])
api_router.include_router(chat_history.router, prefix="/chat-history", tags=["chat-history"])
api_router.include_router(stt.router, prefix="/stt", tags=["stt"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
