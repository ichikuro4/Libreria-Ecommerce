from fastapi import APIRouter
from app.api.routes import root, books, authors, categories, publishers, users

api_router = APIRouter()

# Rutas existentes
api_router.include_router(root.router, tags=["root"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(publishers.router, prefix="/publishers", tags=["publishers"])

# ✅ AGREGAR: Nueva ruta de usuarios
api_router.include_router(users.router, prefix="/users", tags=["users"])