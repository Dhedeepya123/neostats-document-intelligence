from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router
from app.core.database import Base, engine
from app.models.document import Document


app = FastAPI(
    title="Neostats Document Intelligence API",
    description="AI-powered document extraction, validation and API platform",
    version="1.0.0",
)


Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "neostats-document-intelligence",
    }