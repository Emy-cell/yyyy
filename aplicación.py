"""
app.py — Interfaz Visual con Streamlit
Sistema de Control de Inventario y Ventas
==========================================
Estructura de pestañas:
  Inventario      -> Ver, agregar, editar y eliminar productos
  Registrar Venta -> Procesar ventas y descontar stock
  Dashboard       -> Metricas y graficas del mes seleccionado

Ejecutar con:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

import database as db  # módulo de acceso a datos

# ──────────────────────────────────────────────
# ÍCONOS SVG OUTLINE (estilo Lucide/Feather)
# ──────────────────────────────────────────────
def ico(name: str, size: int = 18, color: str = "currentColor") -> str:
    """Retorna el SVG outline del ícono solicitado."""
    s, c = size, color
    _icons = {
        "package":   f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><path d="M12 22L2 17V7l10-5 10 5v10l-10 5z"/><polyline points="2.5 7 12 12 21.5 7"/><line x1="12" y1="12" x2="12" y2="22"/></svg>',
        "cart":      f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
        "bar-chart": f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>',
        "clipboard": f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="15" y2="16"/></svg>',
        "plus":      f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
        "edit":      f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
        "save":      f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>',
        "trash":     f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>',
        "check":     f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "x-circle":  f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
        "info":      f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "award":     f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>',
        "trending":  f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "clock":     f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    }
    return _icons.get(name, "")


# ──────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL DE LA PÁGINA
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Control de Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Paleta de colores y estilos personalizados ──
COLORES = {
    "primario":    "#0F4C81",
    "acento":      "#00C9A7",
    "peligro":     "#FF6B6B",
    "advertencia": "#FFD166",
    "fondo":       "#F7F9FC",
    "texto":       "#1A1A2E",
    "borde":       "#E2E8F0",
}

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .stApp {{ background-color: {COLORES['fondo']}; }}

    .main-header {{
        background: linear-gradient(135deg, {COLORES['primario']} 0%, #1a6faf 100%);
        padding: 2rem 2.5rem; border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(15,76,129,0.18);
    }}
    .main-header h1 {{ color: white; font-size: 2rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }}
    .main-header p  {{ color: rgba(255,255,255,0.80); margin: 0.3rem 0 0; font-size: 0.95rem; }}

    .metric-card {{
        background: white; border: 1px solid {COLORES['borde']};
        border-radius: 14px; padding: 1.4rem 1.6rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }}
    .metric-card .label  {{ font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #718096; margin-bottom: 0.4rem; }}
    .metric-card .value  {{ font-size: 1.9rem; font-weight: 700; color: {COLORES['texto']}; line-height: 1.1; }}
    .metric-card .subtext{{ font-size: 0.82rem; color: #A0AEC0; margin-top: 0.25rem; }}
    .metric-card.accent  {{ border-left: 4px solid {COLORES['acento']}; }}
    .metric-card.danger  {{ border-left: 4px solid {COLORES['peligro']}; }}
    .metric-card.primary {{ border-left: 4px solid {COLORES['primario']}; }}
    .metric-card.warning {{ border-left: 4px solid {COLORES['advertencia']}; }}

    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; border-bottom: 2px solid {COLORES['borde']}; padding-bottom: 0; }}
    .stTabs [data-baseweb="tab"] {{ border-radius: 10px 10px 0 0; padding: 0.6rem 1.4rem; font-weight: 600; font-size: 0.9rem; color: #718096; background: transparent; border: none; }}
    .stTabs [aria-selected="true"] {{ color: {COLORES['primario']} !important; background: white !important; border-bottom: 3px solid {COLORES['primario']} !important; }}

    .stButton > button {{ border-radius: 10px; font-weight: 600; font-size: 0.9rem; padding: 0.55rem 1.4rem; transition: all 0.2s ease; border: none; }}
    .stButton > button:first-child {{ background: {COLORES['primario']}; color: white; }}
    .stButton > button:first-child:hover {{ background: #0d3d6b; box-shadow: 0 4px 12px rgba(15,76,129,0.30); transform: translateY(-1px); }}

    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div {{ border-radius: 10px !important; border: 1.5px solid {COLORES['borde']} !important; }}

    .alert-success {{ background: #F0FFF4; border-left: 4px solid #38A169; padding: 1rem 1.2rem; border-radius: 10px; color: #276749; margin: 1rem 0; display:flex; align-items:flex-start; gap:.6rem; }}
    .alert-error   {{ background: #FFF5F5; border-left: 4px solid {COLORES['peligro']}; padding: 1rem 1.2rem; border-radius: 10px; color: #C53030; margin: 1rem 0; display:flex; align-items:flex-start; gap:.6rem; }}
    .alert-info    {{ background: #EBF8FF; border-left: 4px solid {COLORES['primario']}; padding: 1rem 1.2rem; border-radius: 10px; color: #2C5282; margin: 1rem 0; display:flex; align-items:flex-start; gap:.6rem; }}

    .stDataFrame {{ border-radius: 12px; overflow: hidden; }}
    div[data-testid="stDataFrameResizable"] {{ border-radius: 12px; }}
    hr {{ border-color: {COLORES['borde']}; margin: 1.5rem 0; }}

    .section-title {{ font-size: 1.15rem; font-weight: 700; color: {COLORES['texto']}; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# INICIALIZAR BASE DE DATOS
# ──────────────────────────────────────────────
db.init_db()


# ──────────────────────────────────────────────
# HEADER PRINCIPAL
# ──────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>{ico("package", 32, "white")} Sistema de Control de Inventario y Ventas</h1>
    <p>Gestión centralizada · Análisis en tiempo real · Reportes mensuales</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# PESTAÑAS PRINCIPALES
# ──────────────────────────────────────────────
tab_inv, tab_venta, tab_dash = st.tabs([
    "  Inventario",
    "  Registrar Venta",
    "  Dashboard Mensual",
])


# ════════════════════════════════════════════════
# PESTAÑA 1 — INVENTARIO
# ════════════════════════════════════════════════
with tab_inv:

    productos = db.obtener_productos()
    df_prod   = pd.DataFrame(productos) if productos else pd.DataFrame()

    col1, col2, col3, col4 = st.columns(4)
    total_productos  = len(df_prod) if not df_prod.empty else 0
    total_stock      = int(df_prod["stock"].sum())           if not df_prod.empty else 0
    valor_inventario = (df_prod["precio_compra"] * df_prod["stock"]).sum() if not df_prod.empty else 0
    stock_bajo       = int((df_prod["stock"] <= 5).sum())    if not df_prod.empty else 0

    with col1:
        st.markdown(f"""
        <div class="metric-card primary">
            <div class="label">Total Productos</div>
            <div class="value">{total_productos}</div>
            <div class="subtext">SKUs registrados</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card accent">
            <div class="label">Unidades en Stock</div>
            <div class="value">{total_stock:,}</div>
            <div class="subtext">Total de unidades</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="label">Valor del Inventario</div>
            <div class="value">${valor_inventario:,.2f}</div>
            <div class="subtext">Al precio de costo</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        color_alerta = "danger" if stock_bajo > 0 else "accent"
        st.markdown(f"""
        <div class="metric-card {color_alerta}">
            <div class="label">Stock Bajo (&le; 5)</div>
            <div class="value">{stock_bajo}</div>
            <div class="subtext">Requieren reposición</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_tabla, col_form = st.columns([1.6, 1], gap="large")

    with col_tabla:
        st.markdown(f'<div class="section-title">{ico("clipboard")} Catálogo de Productos</div>',
                    unsafe_allow_html=True)

        if df_prod.empty:
            st.markdown(f"""
            <div class="alert-info">
                {ico("info", 20, "#2C5282")}
                <span>No hay productos registrados aún. Agrega el primero desde el formulario.</span>
            </div>""", unsafe_allow_html=True)
        else:
            df_display = df_prod.rename(columns={
                "codigo":        "Código",
                "nombre":        "Producto",
                "precio_compra": "Costo ($)",
                "precio_venta":  "Precio Venta ($)",
                "stock":         "Stock",
                "fecha_creacion":"Fecha Alta",
            })
            df_display["Margen (%)"] = (
                (df_prod["precio_venta"] - df_prod["precio_compra"])
                / df_prod["precio_compra"] * 100
            ).round(1)

            def resaltar_stock(row):
                if row["Stock"] <= 5:
                    return ["background-color: #FFF5F5"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df_display[["Código","Producto","Costo ($)",
                             "Precio Venta ($)","Margen (%)","Stock","Fecha Alta"]]
                .style
                .apply(resaltar_stock, axis=1)
                .format({"Costo ($)": "${:.2f}", "Precio Venta ($)": "${:.2f}",
                         "Margen (%)": "{:.1f}%"}),
                use_container_width=True,
                height=400,
            )

    with col_form:
        st.markdown(f'<div class="section-title">{ico("plus")} Agregar Producto</div>',
                    unsafe_allow_html=True)

        with st.form("form_agregar", clear_on_submit=True):
            nombre_input = st.text_input("Nombre del Producto", placeholder='Ej: Laptop HP 15"')
            col_a, col_b = st.columns(2)
            with col_a:
                costo_input = st.number_input("Costo ($)", min_value=0.0, step=0.01, format="%.2f")
            with col_b:
                precio_input = st.number_input("Precio Venta ($)", min_value=0.0, step=0.01, format="%.2f")
            stock_input  = st.number_input("Stock Inicial", min_value=0, step=1)

            submitted = st.form_submit_button("+ Agregar Producto", use_container_width=True)

        if submitted:
            try:
                codigo_nuevo = db.agregar_producto(
                    nombre_input, costo_input, precio_input, stock_input
                )
                st.markdown(f"""
                <div class="alert-success">
                    {ico("check", 20, "#276749")}
                    <span>Producto agregado correctamente con código <strong>{codigo_nuevo}</strong>.</span>
                </div>""", unsafe_allow_html=True)
                st.rerun()
            except ValueError as e:
                st.markdown(f"""
                <div class="alert-error">
                    {ico("x-circle", 20, "#C53030")}
                    <span>{e}</span>
                </div>""", unsafe_allow_html=True)

        if not df_prod.empty:
            st.markdown("---")
            st.markdown(f'<div class="section-title">{ico("edit")} Editar / Eliminar</div>',
                        unsafe_allow_html=True)

            opciones = {f"{p['codigo']} — {p['nombre']}": p["codigo"] for p in productos}
            seleccion = st.selectbox("Selecciona un producto", list(opciones.keys()))
            cod_sel   = opciones[seleccion]
            prod_sel  = db.obtener_producto_por_codigo(cod_sel)

            with st.form("form_editar"):
                nombre_e = st.text_input("Nombre",        value=prod_sel["nombre"])
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    costo_e  = st.number_input("Costo ($)",   value=float(prod_sel["precio_compra"]),
                                               min_value=0.0, step=0.01, format="%.2f")
                with col_e2:
                    precio_e = st.number_input("Precio Venta ($)", value=float(prod_sel["precio_venta"]),
                                               min_value=0.0, step=0.01, format="%.2f")
                stock_e  = st.number_input("Stock",        value=int(prod_sel["stock"]),
                                           min_value=0, step=1)

                col_upd, col_del = st.columns(2)
                with col_upd:
                    guardar  = st.form_submit_button("Guardar", use_container_width=True)
                with col_del:
                    eliminar = st.form_submit_button("Eliminar", use_container_width=True)

            if guardar:
                db.actualizar_producto(cod_sel, nombre_e, costo_e, precio_e, stock_e)
                st.success("Producto actualizado.")
                st.rerun()

            if eliminar:
                try:
                    db.eliminar_producto(cod_sel)
                    st.success("Producto eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo eliminar: {e}")


# ════════════════════════════════════════════════
# PESTAÑA 2 — REGISTRAR VENTA
# ════════════════════════════════════════════════
with tab_venta:

    col_vf, col_hist = st.columns([1, 1.8], gap="large")

    with col_vf:
        st.markdown(f'<div class="section-title">{ico("cart")} Nueva Venta</div>',
                    unsafe_allow_html=True)

        productos_activos = db.obtener_productos()
        if not productos_activos:
            st.markdown(f"""
            <div class="alert-info">
                {ico("info", 20, "#2C5282")}
                <span>Debes registrar productos antes de poder crear ventas.</span>
            </div>""", unsafe_allow_html=True)
        else:
            modo = st.radio("Modo de búsqueda", ["Seleccionar de lista", "Ingresar código manual"],
                            horizontal=True)

            if modo == "Seleccionar de lista":
                opciones_v = {f"{p['codigo']} — {p['nombre']} (Stock: {p['stock']})": p["codigo"]
                              for p in productos_activos}
                sel_v      = st.selectbox("Producto", list(opciones_v.keys()))
                cod_venta  = opciones_v[sel_v]
            else:
                cod_venta = st.text_input("Código del producto",
                                          placeholder="PROD-001").strip().upper()

            cantidad_venta = st.number_input("Cantidad", min_value=1, step=1, value=1)

            if cod_venta:
                prod_preview = db.obtener_producto_por_codigo(cod_venta)
                if prod_preview:
                    subtotal   = cantidad_venta * prod_preview["precio_venta"]
                    ganancia_p = cantidad_venta * (prod_preview["precio_venta"] - prod_preview["precio_compra"])
                    st.markdown(f"""
                    <div class="metric-card accent" style="margin: 1rem 0;">
                        <div class="label">Vista Previa</div>
                        <div style="margin-top:.5rem; font-size:.9rem; color:#2D3748; line-height:1.8;">
                            <b>Producto:</b> {prod_preview['nombre']}<br>
                            <b>Precio Unitario:</b> ${prod_preview['precio_venta']:.2f}<br>
                            <b>Stock Disponible:</b> {prod_preview['stock']}<br>
                            <b>Subtotal:</b> ${subtotal:.2f}<br>
                            <b>Ganancia Estimada:</b> ${ganancia_p:.2f}
                        </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="alert-error">
                        {ico("x-circle", 20, "#C53030")}
                        <span>Código no encontrado.</span>
                    </div>""", unsafe_allow_html=True)

            if st.button("Confirmar Venta", use_container_width=True):
                if not cod_venta:
                    st.markdown(f"""
                    <div class="alert-error">
                        {ico("x-circle", 20, "#C53030")}
                        <span>Selecciona o ingresa un código.</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    try:
                        resumen = db.registrar_venta(cod_venta, int(cantidad_venta))
                        st.markdown(f"""
                        <div class="alert-success">
                            {ico("check", 20, "#276749")}
                            <span><b>Venta registrada exitosamente!</b><br>
                            <b>Producto:</b> {resumen['producto']}<br>
                            <b>Cantidad:</b> {resumen['cantidad']} uds.<br>
                            <b>Total cobrado:</b> ${resumen['total']:.2f}<br>
                            <b>Ganancia:</b> ${resumen['ganancia']:.2f}</span>
                        </div>""", unsafe_allow_html=True)
                        st.rerun()
                    except ValueError as e:
                        st.markdown(f"""
                        <div class="alert-error">
                            {ico("x-circle", 20, "#C53030")}
                            <span>{e}</span>
                        </div>""", unsafe_allow_html=True)

    with col_hist:
        st.markdown(f'<div class="section-title">{ico("clock")} Historial de Ventas</div>',
                    unsafe_allow_html=True)

        ventas = db.obtener_ventas()
        if not ventas:
            st.markdown(f"""
            <div class="alert-info">
                {ico("info", 20, "#2C5282")}
                <span>No hay ventas registradas aún.</span>
            </div>""", unsafe_allow_html=True)
        else:
            df_ventas = pd.DataFrame(ventas)
            df_ventas["total"]    = df_ventas["cantidad"] * df_ventas["precio_unitario"]
            df_ventas["ganancia"] = df_ventas["cantidad"] * (
                df_ventas["precio_unitario"] - df_ventas["costo_unitario"]
            )
            df_v_display = df_ventas[
                ["fecha","codigo_producto","nombre_producto","cantidad","precio_unitario","total","ganancia"]
            ].rename(columns={
                "fecha":           "Fecha",
                "codigo_producto": "Código",
                "nombre_producto": "Producto",
                "cantidad":        "Cant.",
                "precio_unitario": "P. Unitario ($)",
                "total":           "Total ($)",
                "ganancia":        "Ganancia ($)",
            })

            st.dataframe(
                df_v_display.style.format({
                    "P. Unitario ($)": "${:.2f}",
                    "Total ($)":       "${:.2f}",
                    "Ganancia ($)":    "${:.2f}",
                }),
                use_container_width=True,
                height=500,
            )


# ════════════════════════════════════════════════
# PESTAÑA 3 — DASHBOARD MENSUAL
# ════════════════════════════════════════════════
with tab_dash:

    hoy = datetime.today()

    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 4])
    with col_sel1:
        meses_nombres = {
            1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril",
            5:"Mayo",  6:"Junio",   7:"Julio", 8:"Agosto",
            9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
        }
        mes_sel  = st.selectbox("Mes", list(meses_nombres.keys()),
                                format_func=lambda x: meses_nombres[x],
                                index=hoy.month - 1)
    with col_sel2:
        anio_sel = st.selectbox("Año", list(range(hoy.year, hoy.year - 5, -1)))

    st.markdown(f'<div class="section-title" style="font-size:1.3rem;">{ico("bar-chart", 22)} Reporte — {meses_nombres[mes_sel]} {anio_sel}</div>',
                unsafe_allow_html=True)
    st.markdown("---")

    metricas  = db.metricas_mes(anio_sel, mes_sel)
    top_prods = db.productos_mas_vendidos(anio_sel, mes_sel, top=10)
    dias_data = db.ganancias_por_dia(anio_sel, mes_sel)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(f"""
        <div class="metric-card primary">
            <div class="label">Unidades Vendidas</div>
            <div class="value">{int(metricas['total_unidades']):,}</div>
            <div class="subtext">Total del mes</div>
        </div>""", unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="metric-card accent">
            <div class="label">Ingresos Brutos</div>
            <div class="value">${metricas['ingresos_brutos']:,.2f}</div>
            <div class="subtext">Ventas brutas</div>
        </div>""", unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="metric-card warning">
            <div class="label">Costo de Ventas</div>
            <div class="value">${metricas['costo_total']:,.2f}</div>
            <div class="subtext">COGS del período</div>
        </div>""", unsafe_allow_html=True)

    with m4:
        color_gan = "accent" if metricas["ganancia_neta"] >= 0 else "danger"
        st.markdown(f"""
        <div class="metric-card {color_gan}">
            <div class="label">Ganancia Neta</div>
            <div class="value">${metricas['ganancia_neta']:,.2f}</div>
            <div class="subtext">Ingresos − Costos</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not top_prods and not dias_data:
        st.markdown(f"""
        <div class="alert-info">
            {ico("info", 20, "#2C5282")}
            <span>No hay ventas registradas para <b>{meses_nombres[mes_sel]} {anio_sel}</b>.
            Registra algunas ventas para ver el dashboard.</span>
        </div>""", unsafe_allow_html=True)
    else:
        col_bar, col_line = st.columns(2, gap="large")

        with col_bar:
            st.markdown(f'<div class="section-title">{ico("award")} Productos Más Vendidos</div>',
                        unsafe_allow_html=True)
            if top_prods:
                df_top = pd.DataFrame(top_prods).sort_values("unidades", ascending=True)
                fig_bar = px.bar(
                    df_top, x="unidades", y="nombre", orientation="h",
                    color="ganancia",
                    color_continuous_scale=["#BEE3F8", "#0F4C81"],
                    labels={"unidades": "Unidades Vendidas", "nombre": "Producto", "ganancia": "Ganancia ($)"},
                    text="unidades",
                )
                fig_bar.update_traces(textposition="outside", textfont_size=12)
                fig_bar.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white", font_family="Inter",
                    coloraxis_colorbar=dict(title="Ganancia ($)"),
                    xaxis=dict(showgrid=True, gridcolor="#EDF2F7", title=""),
                    yaxis=dict(showgrid=False, title=""),
                    margin=dict(l=10, r=10, t=20, b=10), height=380,
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Sin datos de ventas para este período.")

        with col_line:
            st.markdown(f'<div class="section-title">{ico("trending")} Ganancias Diarias</div>',
                        unsafe_allow_html=True)
            if dias_data:
                df_dias = pd.DataFrame(dias_data)
                df_dias["ganancia_acum"] = df_dias["ganancia"].cumsum()

                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=df_dias["dia"], y=df_dias["ganancia"],
                    mode="lines+markers", name="Ganancia del día",
                    line=dict(color=COLORES["acento"], width=3),
                    marker=dict(size=7, color=COLORES["acento"], line=dict(width=2, color="white")),
                    fill="tozeroy", fillcolor="rgba(0,201,167,0.12)",
                ))
                fig_line.add_trace(go.Scatter(
                    x=df_dias["dia"], y=df_dias["ganancia_acum"],
                    mode="lines", name="Acumulado",
                    line=dict(color=COLORES["primario"], width=2.5, dash="dash"),
                ))
                fig_line.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white", font_family="Inter",
                    legend=dict(orientation="h", y=1.05, x=0),
                    xaxis=dict(showgrid=True, gridcolor="#EDF2F7", title="Día"),
                    yaxis=dict(showgrid=True, gridcolor="#EDF2F7", title="Ganancia ($)"),
                    margin=dict(l=10, r=10, t=30, b=10), height=380, hovermode="x unified",
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Sin datos de ganancias para este período.")

        if top_prods:
            st.markdown("---")
            st.markdown(f'<div class="section-title">{ico("clipboard")} Detalle por Producto</div>',
                        unsafe_allow_html=True)
            df_top_full = pd.DataFrame(top_prods)
            df_top_full["margen_%"] = (
                df_top_full["ganancia"] / df_top_full["ingresos"] * 100
            ).round(1)

            st.dataframe(
                df_top_full.rename(columns={
                    "nombre":   "Producto",
                    "unidades": "Uds. Vendidas",
                    "ingresos": "Ingresos ($)",
                    "ganancia": "Ganancia ($)",
                    "margen_%": "Margen (%)",
                }).style.format({
                    "Ingresos ($)": "${:,.2f}",
                    "Ganancia ($)": "${:,.2f}",
                    "Margen (%)":   "{:.1f}%",
                }),
                use_container_width=True,
            )

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#A0AEC0; font-size:0.82rem;'>"
    "Sistema de Inventario y Ventas · Desarrollado con Streamlit + SQLite · "
    f"Sesión activa: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>",
    unsafe_allow_html=True,
)
