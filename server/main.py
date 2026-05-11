from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import get_connection
from models import (ArticuloOut, CompraIn, CompraOut,
                    UsuarioRegister, UsuarioLogin, UsuarioOut, TokenOut)
from auth import hash_password, verify_password, create_access_token, decode_token
from typing import List

app = FastAPI(
    title="Vintage & Streetwear API",
    description="API para la tienda de ropa vintage y streetwear",
    version="2.0.0"
)

# CORS — permite que el frontend (cualquier origen en desarrollo) llame a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # en producción cambiar por la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="/app/images"), name="images")

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependencia que extrae y valida el token JWT del header Authorization."""
    try:
        payload = decode_token(credentials.credentials)
        return payload  # contiene usuario_id y email
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


# ─────────────────────────────────────────────────────────────
# 1. PING-PONG
# ─────────────────────────────────────────────────────────────
@app.get("/ping-pong", tags=["Health"])
def ping_pong():
    return {"message": "pong"}


# ─────────────────────────────────────────────────────────────
# 2. REGISTRO — crea un usuario nuevo y devuelve token
# ─────────────────────────────────────────────────────────────
@app.post("/register", response_model=TokenOut, tags=["Usuarios"])
def register(usuario: UsuarioRegister):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Comprobar si el email ya existe
        cur.execute("SELECT usuario_id FROM usuarios WHERE email = %s", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="El email ya está registrado")

        # Cifrar la contraseña antes de guardarla
        password_hash = hash_password(usuario.password)

        cur.execute("""
            INSERT INTO usuarios (nombre, apellidos, email, telefono, direccion, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING usuario_id, nombre, apellidos, email, telefono, direccion, fecha_registro
        """, (usuario.nombre, usuario.apellidos, usuario.email,
              usuario.telefono, usuario.direccion, password_hash))
        conn.commit()
        row = cur.fetchone()
        cols = ["usuario_id", "nombre", "apellidos", "email", "telefono", "direccion", "fecha_registro"]
        usuario_data = dict(zip(cols, row))

        # Generar token JWT
        token = create_access_token({"usuario_id": usuario_data["usuario_id"], "email": usuario_data["email"]})
        return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────
# 3. LOGIN — devuelve token si las credenciales son correctas
# ─────────────────────────────────────────────────────────────
@app.post("/login", response_model=TokenOut, tags=["Usuarios"])
def login(credenciales: UsuarioLogin):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT usuario_id, nombre, apellidos, email, telefono, direccion, fecha_registro, password_hash
            FROM usuarios WHERE email = %s
        """, (credenciales.email,))
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

        cols = ["usuario_id", "nombre", "apellidos", "email", "telefono", "direccion", "fecha_registro", "password_hash"]
        usuario_data = dict(zip(cols, row))

        if not verify_password(credenciales.password, usuario_data["password_hash"]):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")

        token = create_access_token({"usuario_id": usuario_data["usuario_id"], "email": usuario_data["email"]})
        usuario_data.pop("password_hash")  # nunca se devuelve el hash
        return {"access_token": token, "token_type": "bearer", "usuario": usuario_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────
# 4. PERFIL — devuelve los datos del usuario logueado
# ─────────────────────────────────────────────────────────────
@app.get("/me", response_model=UsuarioOut, tags=["Usuarios"])
def get_me(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT usuario_id, nombre, apellidos, email, telefono, direccion, fecha_registro
            FROM usuarios WHERE usuario_id = %s
        """, (current_user["usuario_id"],))
        row = cur.fetchone()
        cols = ["usuario_id", "nombre", "apellidos", "email", "telefono", "direccion", "fecha_registro"]
        return dict(zip(cols, row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────────────────────
# 5. GET ARTICULOS — catálogo público (no requiere login)
# ─────────────────────────────────────────────────────────────
@app.get("/getArticulos", response_model=List[ArticuloOut], tags=["Artículos"])
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


# ─────────────────────────────────────────────────────────────
# 6. GET COMPRAS — historial del usuario logueado
# ─────────────────────────────────────────────────────────────
@app.get("/getCompraUserId", response_model=List[CompraOut], tags=["Transacciones"])
def get_compra_user_id(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT transaccion_id, fecha, usuario_id, articulo_id,
                   cantidad, tipo_movimiento, coste_total
            FROM transacciones WHERE usuario_id = %s
        """, (current_user["usuario_id"],))
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


# ─────────────────────────────────────────────────────────────
# 7. SET COMPRA — registrar compra del usuario logueado
# ─────────────────────────────────────────────────────────────
@app.post("/setCompraUserId", response_model=CompraOut, tags=["Transacciones"])
def set_compra_user_id(compra: CompraIn, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que el artículo existe
        cur.execute("SELECT articulo_id FROM articulos WHERE articulo_id = %s", (compra.articulo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="El artículo no existe")

        # El usuario_id viene del token, no del body
        cur.execute("""
            INSERT INTO transacciones
                (usuario_id, articulo_id, cantidad, tipo_movimiento, coste_total)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING transaccion_id, fecha, usuario_id, articulo_id,
                      cantidad, tipo_movimiento, coste_total
        """, (current_user["usuario_id"], compra.articulo_id,
              compra.cantidad, compra.tipo_movimiento, compra.coste_total))
        conn.commit()
        row = cur.fetchone()
        cols = ["transaccion_id", "fecha", "usuario_id", "articulo_id",
                "cantidad", "tipo_movimiento", "coste_total"]
        return dict(zip(cols, row))
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
