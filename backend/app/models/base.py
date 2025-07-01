"""
Enums y clases base compartidas
"""

from enum import Enum

class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pendiente_pago"
    PAID = "pagado"
    PROCESSING = "procesando"
    SHIPPED = "enviado"
    DELIVERED = "entregado"
    CANCELLED = "cancelado"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class UserRole(str, Enum):
    CUSTOMER = "cliente"
    ADMIN = "admin"
    STAFF = "staff"

class DiscountType(str, Enum):
    PERCENTAGE = "porcentaje"
    FIXED_AMOUNT = "monto_fijo"

class TipoDocumento(str, Enum):
    DNI = "DNI"
    RUC = "RUC"
    CE = "CE"  # Carné de Extranjería

class Genero(str, Enum):
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    NO_ESPECIFICADO = "no_especificado"