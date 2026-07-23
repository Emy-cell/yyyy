"""
database.py — Capa de acceso a datos
Sistema de Control de Inventario y Ventas
==========================================
Maneja todas las operaciones con SQLite:
  - Creación de tablas (Productos, Ventas)
  - CRUD de productos
  - Registro de ventas y descuento de stock
  - Consultas para el dashboard mensual
"""

import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
DB_PATH = "inventario.db"


# ──────────────────────────────────────────────
# CONEXIÓN
# ──────────────────────────────────────────────
@contextmanager
def get_connection():
    """Context manager que abre/cierra la conexión de forma segura."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # permite acceso por nombre de columna
    conn.execute("PRAGMA foreign_keys = ON") # activa integridad referencial
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ──────────────────────────────────────────────
# INICIALIZACIÓN DE TABLAS
# ──────────────────────────────────────────────
def init_db():
    """Crea las tablas si no existen. Se llama al arrancar la app."""
    with get_connection() as conn:
        conn.executescript("""
            -- ── Tabla de Productos ──────────────────────────────
            CREATE TABLE IF NOT EXISTS productos (
                codigo          TEXT PRIMARY KEY,   -- PROD-001, PROD-002 …
                nombre          TEXT NOT NULL,
                precio_compra   REAL NOT NULL CHECK(precio_compra >= 0),
                precio_venta    REAL NOT NULL CHECK(precio_venta  >= 0),
                stock           INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                fecha_creacion  TEXT NOT NULL
            );

            -- ── Tabla de Ventas ──────────────────────────────────
            CREATE TABLE IF NOT EXISTS ventas (
                id              TEXT PRIMARY KEY,   -- UUID único por venta
                codigo_producto TEXT NOT NULL REFERENCES productos(codigo),
                cantidad        INTEGER NOT NULL CHECK(cantidad > 0),
                precio_unitario REAL NOT NULL,      -- precio de venta al momento
                costo_unitario  REAL NOT NULL,      -- precio de compra al momento
                fecha           TEXT NOT NULL       -- ISO-8601: YYYY-MM-DD HH:MM:SS
            );
        """)


# ──────────────────────────────────────────────
# GENERADOR DE CÓDIGOS SECUENCIALES
# ──────────────────────────────────────────────
def _generar_codigo() -> str:
    """
    Devuelve el siguiente código disponible en formato PROD-NNN.
    Examina el máximo número existente y suma 1.
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT codigo FROM productos ORDER BY codigo DESC LIMIT 1"
        ).fetchone()

    if row is None:
        return "PROD-001"

    ultimo = row["codigo"]          # e.g. "PROD-007"
    numero = int(ultimo.split("-")[1]) + 1
    return f"PROD-{numero:03d}"


# ──────────────────────────────────────────────
# OPERACIONES DE PRODUCTOS
# ──────────────────────────────────────────────
def agregar_producto(nombre: str, precio_compra: float,
                     precio_venta: float, stock: int) -> str:
    """
    Inserta un nuevo producto y retorna el código asignado.
    Lanza ValueError si los datos son inválidos.
    """
    if not nombre.strip():
        raise ValueError("El nombre del producto no puede estar vacío.")
    if precio_compra < 0 or precio_venta < 0:
        raise ValueError("Los precios deben ser valores positivos.")
    if stock < 0:
        raise ValueError("El stock inicial no puede ser negativo.")

    codigo = _generar_codigo()
    fecha  = datetime.now().isoformat(sep=" ", timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO productos
               (codigo, nombre, precio_compra, precio_venta, stock, fecha_creacion)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (codigo, nombre.strip(), precio_compra, precio_venta, stock, fecha)
        )
    return codigo


def obtener_productos() -> list[dict]:
    """Devuelve todos los productos ordenados por código."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM productos ORDER BY codigo"
        ).fetchall()
    return [dict(r) for r in rows]


def obtener_producto_por_codigo(codigo: str) -> dict | None:
    """Busca un producto exacto por su código. Retorna None si no existe."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM productos WHERE codigo = ?", (codigo.strip().upper(),)
        ).fetchone()
    return dict(row) if row else None


def actualizar_producto(codigo: str, nombre: str, precio_compra: float,
                        precio_venta: float, stock: int):
    """Actualiza todos los campos editables de un producto existente."""
    with get_connection() as conn:
        conn.execute(
            """UPDATE productos
               SET nombre=?, precio_compra=?, precio_venta=?, stock=?
               WHERE codigo=?""",
            (nombre.strip(), precio_compra, precio_venta, stock, codigo)
        )


def eliminar_producto(codigo: str):
    """
    Elimina un producto. Lanza IntegrityError si tiene ventas asociadas
    (gracias a la FOREIGN KEY con ON DELETE RESTRICT implícito).
    """
    with get_connection() as conn:
        conn.execute("DELETE FROM productos WHERE codigo = ?", (codigo,))


# ──────────────────────────────────────────────
# OPERACIONES DE VENTAS
# ──────────────────────────────────────────────
def registrar_venta(codigo_producto: str, cantidad: int) -> dict:
    """
    Registra una venta y descuenta el stock en una transacción atómica.
    Retorna un dict con el resumen de la venta.
    Lanza ValueError si el stock es insuficiente o el producto no existe.
    """
    with get_connection() as conn:
        # 1. Bloquear el registro del producto para esta transacción
        producto = conn.execute(
            "SELECT * FROM productos WHERE codigo = ?", (codigo_producto,)
        ).fetchone()

        if producto is None:
            raise ValueError(f"No existe el producto con código '{codigo_producto}'.")

        if producto["stock"] < cantidad:
            raise ValueError(
                f"Stock insuficiente. Disponible: {producto['stock']} unidades."
            )

        # 2. Insertar la venta
        venta_id = str(uuid.uuid4())
        fecha    = datetime.now().isoformat(sep=" ", timespec="seconds")

        conn.execute(
            """INSERT INTO ventas
               (id, codigo_producto, cantidad, precio_unitario, costo_unitario, fecha)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (venta_id, codigo_producto, cantidad,
             producto["precio_venta"], producto["precio_compra"], fecha)
        )

        # 3. Descontar stock
        conn.execute(
            "UPDATE productos SET stock = stock - ? WHERE codigo = ?",
            (cantidad, codigo_producto)
        )

    return {
        "id":             venta_id,
        "producto":       producto["nombre"],
        "codigo":         codigo_producto,
        "cantidad":       cantidad,
        "precio_unitario": producto["precio_venta"],
        "total":          cantidad * producto["precio_venta"],
        "ganancia":       cantidad * (producto["precio_venta"] - producto["precio_compra"]),
        "fecha":          fecha,
    }


def obtener_ventas() -> list[dict]:
    """Devuelve todas las ventas enriquecidas con el nombre del producto."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT v.*, p.nombre AS nombre_producto
               FROM ventas v
               JOIN productos p ON p.codigo = v.codigo_producto
               ORDER BY v.fecha DESC"""
        ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# CONSULTAS PARA EL DASHBOARD MENSUAL
# ──────────────────────────────────────────────
def metricas_mes(anio: int, mes: int) -> dict:
    """
    Calcula métricas clave del mes dado:
      - total_unidades: suma de unidades vendidas
      - ingresos_brutos: suma(cantidad × precio_unitario)
      - costo_total:     suma(cantidad × costo_unitario)
      - ganancia_neta:   ingresos_brutos − costo_total
    """
    prefijo = f"{anio}-{mes:02d}"

    with get_connection() as conn:
        row = conn.execute(
            """SELECT
                 COALESCE(SUM(cantidad), 0)                           AS total_unidades,
                 COALESCE(SUM(cantidad * precio_unitario), 0)         AS ingresos_brutos,
                 COALESCE(SUM(cantidad * costo_unitario),  0)         AS costo_total,
                 COALESCE(SUM(cantidad * (precio_unitario - costo_unitario)), 0) AS ganancia_neta
               FROM ventas
               WHERE fecha LIKE ?""",
            (f"{prefijo}%",)
        ).fetchone()

    return dict(row)


def productos_mas_vendidos(anio: int, mes: int, top: int = 10) -> list[dict]:
    """Top-N productos por unidades vendidas en el mes."""
    prefijo = f"{anio}-{mes:02d}"

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT p.nombre,
                      SUM(v.cantidad)                              AS unidades,
                      SUM(v.cantidad * v.precio_unitario)          AS ingresos,
                      SUM(v.cantidad*(v.precio_unitario-v.costo_unitario)) AS ganancia
               FROM ventas v
               JOIN productos p ON p.codigo = v.codigo_producto
               WHERE v.fecha LIKE ?
               GROUP BY v.codigo_producto
               ORDER BY unidades DESC
               LIMIT ?""",
            (f"{prefijo}%", top)
        ).fetchall()

    return [dict(r) for r in rows]


def ganancias_por_dia(anio: int, mes: int) -> list[dict]:
    """Ganancia neta agrupada por día del mes (para gráfica de líneas)."""
    prefijo = f"{anio}-{mes:02d}"

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT SUBSTR(fecha, 1, 10)                                   AS dia,
                      SUM(cantidad * (precio_unitario - costo_unitario))     AS ganancia
               FROM ventas
               WHERE fecha LIKE ?
               GROUP BY dia
               ORDER BY dia""",
            (f"{prefijo}%",)
        ).fetchall()

    return [dict(r) for r in rows]
