"""Excepciones de dominio y negocio para Inventario Personal."""


class AppException(Exception):
    """Excepción base para errores de negocio en la aplicación."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundError(AppException):
    """Lanzada cuando una entidad solicitada no existe."""
    pass


class ProductNotFoundError(EntityNotFoundError):
    """Lanzada cuando un producto no existe o no pertenece al usuario autenticado."""
    def __init__(self, message: str = "Producto no encontrado"):
        super().__init__(message)


class InvariantViolationError(AppException):
    """Lanzada cuando una operación vulnera un invariante o regla estricta de negocio."""
    pass


class AuthenticationError(AppException):
    """Lanzada cuando fallan las credenciales o la autenticación del usuario."""
    def __init__(self, message: str = "Credenciales inválidas"):
        super().__init__(message)


class AccessDeniedError(AppException):
    """Lanzada cuando un usuario intenta acceder a recursos no autorizados."""
    def __init__(self, message: str = "Acceso no autorizado"):
        super().__init__(message)


class DuplicateEntityError(AppException):
    """Lanzada cuando se intenta crear o renombrar una entidad con un identificador o nombre duplicado."""
    pass


class ConfirmationRequiredError(AppException):
    """Lanzada cuando una acción destructiva requiere confirmación explícita del usuario."""
    def __init__(self, message: str = "Se requiere confirmación explícita para eliminar el producto"):
        super().__init__(message)
