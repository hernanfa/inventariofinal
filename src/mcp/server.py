"""Servidor Model Context Protocol (MCP) para Inventario Personal."""

from typing import Any, Dict, Optional
from fastmcp import FastMCP

from src.mcp.tools import (
    consultar_inventario as tool_consultar_inventario,
    consultar_productos_stock_bajo as tool_consultar_stock_bajo,
)

mcp = FastMCP("InventarioPersonal")


@mcp.tool()
def consultar_inventario(
    token: str,
    solo_stock_bajo: bool = False,
    busqueda: Optional[str] = None,
) -> Dict[str, Any]:
    """Consulta los productos del inventario personal del usuario autenticado."""
    return tool_consultar_inventario(
        token=token,
        solo_stock_bajo=solo_stock_bajo,
        busqueda=busqueda,
    )


@mcp.tool()
def consultar_productos_stock_bajo(token: str) -> Dict[str, Any]:
    """Obtiene únicamente los productos del usuario autenticado con existencias críticas o bajas."""
    return tool_consultar_stock_bajo(token=token)


def main() -> None:
    """Punto de entrada para ejecutar el servidor MCP."""
    from src.models.base import Base, engine

    Base.metadata.create_all(bind=engine)
    mcp.run()


if __name__ == "__main__":
    main()
