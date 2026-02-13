from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def log_requests(request, call_next):
    import time
    import traceback
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        print(f"Path: {request.url.path} Method: {request.method} Status: {response.status_code} Time: {process_time:.4f}s")
        return response
    except Exception as e:
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        from fastapi import responses
        return responses.JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/")
def root():
    return {"message": "Welcome to Medical Chatbot RAG API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
