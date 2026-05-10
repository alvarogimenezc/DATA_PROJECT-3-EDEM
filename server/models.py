from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArticuloOut(BaseModel):
    articulo_id: int
    nombre: Optional[str]
    descripcion: Optional[str]
    estado: Optional[str]
    categoria: Optional[str]
    unidad_medida: Optional[str]
    precio_unitario: Optional[float]
    url_imagen: Optional[str]

class CompraIn(BaseModel):
    usuario_id: int
    articulo_id: int
    cantidad: float
    tipo_movimiento: str
    coste_total: float

class CompraOut(BaseModel):
    transaccion_id: int
    fecha: Optional[datetime]
    usuario_id: int
    articulo_id: int
    cantidad: float
    tipo_movimiento: Optional[str]
    coste_total: Optional[float]