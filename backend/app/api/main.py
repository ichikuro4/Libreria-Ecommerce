# backend/app/api/main.py
"""
Router principal de la API - Versión simplificada
"""

from fastapi import APIRouter
from app.api.routes import (
    root, auth, users, books, authors, categories, publishers,
    orders, promotions, reviews
)

api_router = APIRouter()

# Rutas existentes
api_router.include_router(root.router, tags=["root"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(authors.router, prefix="/authors", tags=["authors"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(publishers.router, prefix="/publishers", tags=["publishers"])

# ✅ NUEVAS RUTAS E-COMMERCE
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(promotions.router, prefix="/promotions", tags=["promotions"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])