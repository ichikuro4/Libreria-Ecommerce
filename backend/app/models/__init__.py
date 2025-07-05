"""
Exportar todos los modelos para fácil importación
"""

# Base y Enums
from .base import OrderStatus, PaymentStatus, UserRole, DiscountType, TipoDocumento, Genero

# User models
from .user_models import (
    User, UserCreate, UserRead, UserUpdate, UserChangePassword, 
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest, ChangePasswordRequest,
    Address, AddressCreate, AddressRead, AddressUpdate
)

# Book models
from .book_models import (
    Book, BookCreate, BookRead, BookUpdate,
    Author, AuthorCreate, AuthorRead, AuthorUpdate,
    Category, CategoryCreate, CategoryRead, CategoryUpdate,
    Publisher, PublisherCreate, PublisherRead, PublisherUpdate,
    BookAuthor, BookCategory
)

# Order models
from .order_models import (
    Order, OrderCreate, OrderRead, OrderUpdate,
    OrderDetail, OrderDetailCreate, OrderDetailRead
)

# Promotion models
from .promotion_models import (
    Promotion, PromotionCreate, PromotionRead, PromotionUpdate,
    Coupon, CouponCreate, CouponRead, CouponUpdate,
    # Junction tables
    PromotionBook, PromotionCategory
)

# Review models
from .review_models import (
    Review, ReviewCreate, ReviewRead, ReviewUpdate,
    WishList, WishListCreate, WishListRead
)

__all__ = [
    # Base
    'OrderStatus', 'PaymentStatus', 'UserRole', 'DiscountType', 'TipoDocumento', 'Genero',
    
    # Users
    'User', 'UserCreate', 'UserRead', 'UserUpdate', 
    'UserChangePassword', 'UserRegister', 'UserLogin',
    'Address', 'AddressCreate', 'AddressRead', 'AddressUpdate',
    
    # Books
    'Book', 'BookCreate', 'BookRead', 'BookUpdate',
    'Author', 'AuthorCreate', 'AuthorRead', 'AuthorUpdate',
    'Category', 'CategoryCreate', 'CategoryRead', 'CategoryUpdate',
    'Publisher', 'PublisherCreate', 'PublisherRead', 'PublisherUpdate',
    'BookAuthor', 'BookCategory',
    
    # Orders
    'Order', 'OrderCreate', 'OrderRead', 'OrderUpdate',
    'OrderDetail', 'OrderDetailCreate', 'OrderDetailRead',
    
    # Promotions
    'Promotion', 'PromotionCreate', 'PromotionRead', 'PromotionUpdate',
    'Coupon', 'CouponCreate', 'CouponRead', 'CouponUpdate',
    'PromotionBook', 'PromotionCategory',
    
    # Reviews
    'Review', 'ReviewCreate', 'ReviewRead', 'ReviewUpdate',
    'WishList', 'WishListCreate', 'WishListRead',
    
    # Auth models
    'TokenResponse', 'RefreshTokenRequest', 'ChangePasswordRequest',
]