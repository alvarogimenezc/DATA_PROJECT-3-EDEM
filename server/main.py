import os
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import get_connection
from models import ArticuloOut, CompraIn, CompraOut

load_dotenv()

security = HTTPBearer()
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN", "dev-token")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.scheme.lower() != "bearer" or credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido"
        )


app = FastAPI(
    title="Vintage & Streetwear API",
    description="API para la tienda de ropa vintage y streetwear",
    version="1.0.0"
)

# ─────────────────────────────────────────
# 1. PING-PONG
# ─────────────────────────────────────────
@app.get("/ping-pong", tags=["Health"])
def ping_pong():
    return {"message": "pong"}


# ─────────────────────────────────────────
# 2. GET ARTICULOS
# ─────────────────────────────────────────
@app.get("/getArticulos", response_model=List[ArticuloOut], tags=["Articulos"], dependencies=[Depends(verify_token)])
def get_articulos():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT articulo_id, nombre, descripcion, estado,
                   categoria, unidad_medida, precio_unitario, url_imagen
            FROM articulos
        """)
        rows = cur.fetchall()
        cols = ["articulo_id", "nombre", "descripcion", "estado",
                "categoria", "unidad_medida", "precio_unitario", "url_imagen"]
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────
# 3. GET COMPRA USER ID
# ─────────────────────────────────────────
@app.get("/getCompraUserId/{usuario_id}", response_model=List[CompraOut], tags=["Transacciones"], dependencies=[Depends(verify_token)])
def get_compra_user_id(usuario_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT transaccion_id, fecha, usuario_id, articulo_id,
                   cantidad, tipo_movimiento, coste_total
            FROM transacciones
            WHERE usuario_id = %s
        """, (usuario_id,))
        rows = cur.fetchall()
        cols = ["transaccion_id", "fecha", "usuario_id", "articulo_id",
                "cantidad", "tipo_movimiento", "coste_total"]
        if not rows:
            raise HTTPException(status_code=404, detail="No hay compras para este usuario")
        return [dict(zip(cols, row)) for row in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────
# 4. SET COMPRA USER ID
# ─────────────────────────────────────────
@app.post("/setCompraUserId", response_model=CompraOut, tags=["Transacciones"], dependencies=[Depends(verify_token)])
def set_compra_user_id(compra: CompraIn):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT 1 FROM usuarios WHERE usuario_id = %s", (compra.usuario_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="El usuario no existe")

        cur.execute("SELECT 1 FROM articulos WHERE articulo_id = %s", (compra.articulo_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="El articulo no existe")

        cur.execute("""
            INSERT INTO transacciones
                (usuario_id, articulo_id, cantidad, tipo_movimiento, coste_total)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING transaccion_id, fecha, usuario_id, articulo_id,
                      cantidad, tipo_movimiento, coste_total
        """, (
            compra.usuario_id,
            compra.articulo_id,
            compra.cantidad,
            compra.tipo_movimiento,
            compra.coste_total
        ))
        row = cur.fetchone()
        conn.commit()

        cols = ["transaccion_id", "fecha", "usuario_id", "articulo_id",
                "cantidad", "tipo_movimiento", "coste_total"]
        return dict(zip(cols, row))

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        cur.close()
        conn.close()