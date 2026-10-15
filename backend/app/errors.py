"""
NezaMateriales — Excepciones personalizadas.

Todas retornan JSON consistente:
    { "status": "error", "message": "..." }

Convención definida en AGENTS.md.
"""


class NezaException(Exception):
    """Excepción base de NezaMateriales."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CalculationError(NezaException):
    """Error en el motor de cálculo de rendimiento de materiales."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=422)


class ProductNotFoundError(NezaException):
    """Producto no encontrado en el catálogo."""

    def __init__(self, product_id: int) -> None:
        super().__init__(
            message=f"Producto con id={product_id} no encontrado.",
            status_code=404,
        )


class QuoteNotFoundError(NezaException):
    """Cotización no encontrada."""

    def __init__(self, folio: str) -> None:
        super().__init__(
            message=f"Cotización con folio={folio} no encontrada.",
            status_code=404,
        )
