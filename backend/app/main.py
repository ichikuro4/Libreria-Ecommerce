from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from app.db.connection import engine
from app.api.main import api_router  
from app.models import (
    Author, Category, Publisher, Book, BookAuthor
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application Startup: Initialize resources.")
    async with engine.begin() as conn:
        # Eliminar y crear todas las tablas en startup
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    print("Application Shutdown: Cleanup resources.")

app = FastAPI(
    title="Librería E-commerce API",
    version="1.0.0",
    description="API REST para e-commerce de librería",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

origins = [
    'http://0.0.0.0:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',  # React frontend
    'http://localhost:5173',  # Vite frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # En desarrollo
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Incluir rutas (cuando las creemos)
app.include_router(api_router, prefix='/api')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, reload=True)