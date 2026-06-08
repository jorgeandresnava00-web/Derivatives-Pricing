"""Dashboard del Valuador de Futuros — Paso 9.6 (rediseño "terminal").

Estética y layout fieles al mockup (`Mockup.png`): una sola pantalla,
estilo terminal monoespaciado, y vista de UN instrumento a la vez con un
switcher. El dashboard SOLO lee y dibuja el CSV; no calcula valuaciones
(eso es trabajo de run.py). Separación de responsabilidades.

Mapa de paneles (igual que el mockup):
  ┌ Barra superior: marca · fecha · instrumento · estado ──────────────┐
  │ KPI señal │ KPI basis prom │ KPI días venc │  Cálculo F_teórico     │
  │ Switcher + tira de métricas (spot/mercado/teórico/basis) + acción  │
  │ Convergencia del contrato        │  Basis en el tiempo vs banda     │
  │ Histórico del instrumento        │  Proximidad a señal de arbitraje │
  └ Barra de estado inferior ──────────────────────────────────────────┘
"""
import math
from datetime import date

import plotly.graph_objects as go
import streamlit as st
import yaml

from src.maturity import proximo_vencimiento
from src.storage import cargar_historico

# ── Bloque 0: Setup ──────────────────────────────────────────────────
st.set_page_config(page_title="Valuador de Futuros", layout="wide")

# ── Paleta (centralizada para reusar en CSS y en las gráficas Plotly) ─
COL = {
    "bg":        "#16161B",   # fondo de la página (charcoal profundo)
    "panel":     "#21212A",   # fondo de cada panel
    "border":    "#34343E",   # borde sutil de los paneles
    "ink":       "#E8E8EA",   # texto principal
    "muted":     "#8B8B96",   # texto secundario / etiquetas
    "orange":    "#F5821F",   # acento (títulos, futuro de mercado)
    "green":     "#34D399",   # positivo / señal / futuro teórico
    "teal":      "#2DD4BF",   # spot
    "amber":     "#FBBF24",   # alerta media
    "red":       "#F87171",   # negativo / vender / fuera de banda
    "grid":      "#2C2C35",   # líneas de la cuadrícula en gráficas
}

MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
         "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def fmt_fecha(iso: str) -> str:
    """'2026-06-05' → '05/06/2026' (formato del mockup)."""
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def fmt_venc(d: date) -> str:
    """date → '20 JUN 2026' (mes en español, mayúsculas)."""
    return f"{d.day:02d} {MESES[d.month - 1]} {d.year}"


# ── Bloque 1: CSS — estética terminal + layout compacto ──────────────
# Inyectamos una capa CSS para: fuente monoespaciada, paneles con borde,
# y MUCHA compresión de paddings para que todo quepa sin scroll.
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');

    .stApp {{ background:{COL['bg']}; }}
    html, body, [class*="css"] {{
        font-family:'JetBrains Mono', Consolas, monospace !important;
        color:{COL['ink']};
    }}
    /* Contenedor principal con aire (se permite un poco de scroll) */
    .block-container {{ padding:0.9rem 1.2rem 0.8rem 1.2rem !important; max-width:100% !important; }}
    /* Separación generosa entre filas y columnas para que los paneles "respiren" */
    div[data-testid="stVerticalBlock"] {{ gap:0.9rem !important; }}
    div[data-testid="stHorizontalBlock"] {{ gap:0.9rem !important; }}
    header[data-testid="stHeader"] {{ display:none; }}
    #MainMenu, footer {{ visibility:hidden; }}

    /* Panel genérico (tarjeta con borde y título naranja) */
    .panel {{
        background:{COL['panel']}; border:1px solid {COL['border']};
        border-radius:8px; padding:10px 14px; height:100%;
    }}
    .panel-title {{
        color:{COL['orange']}; font-size:0.72rem; font-weight:700;
        letter-spacing:0.12em; text-transform:uppercase; margin-bottom:6px;
    }}
    .panel-title .num {{ color:{COL['muted']}; margin-right:6px; }}

    /* Contenedor con borde de Streamlit (st.container(border=True)) → look de panel */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background:{COL['panel']}; border:1px solid {COL['border']} !important;
        border-radius:8px; padding:10px 14px;
    }}

    /* Barra superior */
    .topbar {{
        display:flex; justify-content:space-between; align-items:center;
        background:{COL['panel']}; border:1px solid {COL['border']};
        border-radius:8px; padding:8px 16px; margin-bottom:2px;
    }}
    .brand {{ color:{COL['orange']}; font-size:1.15rem; font-weight:700; }}
    .brand small {{ color:{COL['muted']}; font-size:0.7rem; font-weight:400; display:block; }}
    .topfield {{ padding:0 18px; border-left:1px solid {COL['border']}; }}
    .topfield .lbl {{ color:{COL['muted']}; font-size:0.6rem; letter-spacing:0.1em; }}
    .topfield .val {{ color:{COL['ink']}; font-size:0.82rem; font-weight:600; }}

    /* KPI grandes */
    .kpi-big {{ font-size:2.0rem; font-weight:700; line-height:1.1; }}
    .kpi-sub {{ color:{COL['muted']}; font-size:0.68rem; }}

    /* Semáforo (KPI señal) */
    .light {{ display:flex; flex-direction:column; gap:4px; align-items:center; }}
    .bulb {{ width:14px; height:14px; border-radius:50%; background:#2a2a32; }}

    /* Tira de métricas del instrumento */
    .metric-lbl {{ color:{COL['muted']}; font-size:0.62rem; letter-spacing:0.08em; }}
    .metric-val {{ font-size:1.25rem; font-weight:700; }}
    .metric-note {{ color:{COL['muted']}; font-size:0.6rem; }}

    /* Botón de acción sugerida */
    .action {{
        border-radius:6px; padding:8px 12px; text-align:center;
        font-weight:700; font-size:0.95rem;
    }}

    /* Tabla histórico */
    table.blotter {{ width:100%; border-collapse:collapse; font-size:0.72rem; }}
    table.blotter th {{
        color:{COL['muted']}; text-align:right; font-weight:600;
        border-bottom:1px solid {COL['border']}; padding:3px 8px;
        letter-spacing:0.06em;
    }}
    table.blotter td {{ text-align:right; padding:3px 8px; color:{COL['ink']}; }}
    table.blotter td.fecha {{ text-align:left; color:{COL['muted']}; }}
    .badge {{ padding:1px 8px; border-radius:4px; font-weight:700; font-size:0.66rem; }}

    /* Barra de estado inferior */
    .statusbar {{
        display:flex; gap:0; background:{COL['panel']};
        border:1px solid {COL['border']}; border-radius:8px;
        padding:6px 16px; margin-top:2px; font-size:0.66rem;
    }}
    .statusbar .seg {{ padding:0 18px; border-right:1px solid {COL['border']}; }}
    .statusbar .seg:last-child {{ border-right:none; }}
    .statusbar .lbl {{ color:{COL['muted']}; letter-spacing:0.08em; }}

    /* Switcher (radio horizontal con look de tabs) */
    div[role="radiogroup"] {{ gap:6px; }}
    div[role="radiogroup"] label {{
        background:{COL['panel']}; border:1px solid {COL['border']};
        border-radius:6px; padding:2px 14px;
    }}
    /* Ocultar el círculo del radio: queremos look de "tabs", no de radio */
    div[role="radiogroup"] label > div:first-child {{ display:none !important; }}
    /* Resaltar la pestaña activa (la que tiene el texto en naranja) */
    div[role="radiogroup"] label:has(input:checked) {{
        border-color:{COL['orange']}; background:#2c2620;
    }}
    div[role="radiogroup"] label p {{ font-size:0.72rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Bloque 2: Cargar config y datos ──────────────────────────────────
with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

df = cargar_historico(cfg["ruta_csv"])

# Código defensivo: sin datos, avisamos y paramos antes de dibujar nada.
if df.empty:
    st.title("Valuador de Futuros")
    st.warning("Aún no hay datos. Corre `python run.py` para generar el primer registro.")
    st.stop()

hoy = df["fecha"].max()
hoy_date = date.fromisoformat(hoy)
banda = cfg["banda_costos"]                 # 0.005
instrumentos = cfg["instrumentos"]


# ── Bloque 3: Switcher de instrumento (vista de uno a la vez) ────────
# Etiquetas legibles ("E-mini S&P 500 (ES=F)") pero recuperamos el ticker.
opciones = {f"{p['nombre']} ({tk})": tk for tk, p in instrumentos.items()}
elegido_lbl = st.radio("Instrumento", list(opciones), horizontal=True,
                       label_visibility="collapsed")
ticker = opciones[elegido_lbl]
params = instrumentos[ticker]

# Serie histórica del instrumento elegido (ascendente por fecha).
d = df[df["ticker"] == ticker].sort_values("fecha").reset_index(drop=True)
# basis "carry" = Futuro de mercado − Spot (el del mockup, en puntos).
d["basis_fs"] = d["F_mercado"] - d["spot"]

fila = d.iloc[-1]                            # el día más reciente
spot   = fila["spot"]
F_mkt  = fila["F_mercado"]
F_teo  = fila["F_teorico"]
mispr  = fila["basis"]                       # CSV basis = F_mercado − F_teórico
basis_fs = fila["basis_fs"]
r, q, u, T = fila["r"], params["q"], params["u"], fila["T"]
señal = fila["señal"]

# Estadística para las bandas σ (sobre el basis carry de la ventana).
mu  = d["basis_fs"].mean()
sd  = max(d["basis_fs"].std(ddof=0), 1e-9)   # guard: evita /0 con 1 fila
d["z"] = (d["basis_fs"] - mu) / sd

# Métricas derivadas para los KPIs.
dias_venc = int(round(T * 365))
venc_date = proximo_vencimiento(desde=hoy_date)
basis_prom = d["basis_fs"].tail(20).mean()
banda_pts = banda * F_teo                     # banda de no-arbitraje en puntos
desviacion = abs(mispr) - banda_pts           # cuánto excede |mispricing| la banda
carry_impl = math.log(F_mkt / spot) / T if (spot > 0 and T > 0) else 0.0

# Mapa de la señal → acción, color y narrativa.
if señal == "VENDE FUTURO":
    accion_txt, accion_col = "Vender Futuro", COL["red"]
    accion_nota = "El futuro cotiza por encima del teórico (sobrevalorado)."
    hay_señal, dir_txt = True, "por encima"
elif señal == "COMPRA FUTURO":
    accion_txt, accion_col = "Comprar Futuro", COL["green"]
    accion_nota = "El futuro cotiza por debajo del teórico (infravalorado)."
    hay_señal, dir_txt = True, "por debajo"
else:
    accion_txt, accion_col = "Mantener", COL["muted"]
    accion_nota = "El futuro cotiza dentro de la banda de no-arbitraje."
    hay_señal, dir_txt = False, "por encima" if mispr >= 0 else "por debajo"

# Nivel de mispricing (etiqueta cualitativa para la tira inferior).
ratio = abs(mispr) / banda_pts if banda_pts else 0
if ratio >= 2:   mispr_lvl, mispr_col = "Alto", COL["red"]
elif ratio >= 1: mispr_lvl, mispr_col = "Moderado", COL["amber"]
else:            mispr_lvl, mispr_col = "Bajo", COL["muted"]


def sigma_color(z: float) -> str:
    """Color por número de desviaciones estándar (leyenda del mockup)."""
    if z > 2:    return COL["red"]
    if z > 1:    return COL["orange"]
    if z > 0:    return COL["amber"]
    if z > -1:   return COL["teal"]
    return COL["green"]


# ── Bloque 4: Barra superior ─────────────────────────────────────────
st.markdown(
    f"""
    <div class="topbar">
      <div class="brand">Valuador de Futuros
        <small>Dashboard de arbitraje y convergencia</small></div>
      <div style="display:flex;align-items:center;">
        <div class="topfield"><div class="lbl">FECHA</div>
             <div class="val">{fmt_fecha(hoy)}</div></div>
        <div class="topfield"><div class="lbl">CIERRE</div>
             <div class="val">EOD</div></div>
        <div class="topfield"><div class="lbl">INSTRUMENTO</div>
             <div class="val">{params['nombre']} ({ticker})</div></div>
        <div class="topfield"><div class="lbl">ESTADO DEL MERCADO</div>
             <div class="val" style="color:{COL['green']};">● CERRADO · EOD</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Bloque 5: Fila de KPIs + panel de fórmula ────────────────────────
top_l, top_r = st.columns([2.35, 1])

with top_l:
    k1, k2, k3 = st.columns(3)

    # KPI 1 — Semáforo de señal de arbitraje.
    luz_si = COL["green"] if hay_señal else "#2a2a32"
    luz_no = "#2a2a32" if hay_señal else COL["muted"]
    dev_txt = (f"{desviacion:+.2f} pts ({dir_txt})" if hay_señal
               else f"dentro de banda (faltan {-desviacion:.2f} pts)")
    with k1:
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title"><span class="num">1</span>Señal de arbitraje</div>
              <div style="display:flex;align-items:center;gap:14px;">
                <div class="light">
                  <div class="bulb" style="background:{COL['red'] if (hay_señal and señal=='VENDE FUTURO') else '#2a2a32'};"></div>
                  <div class="bulb" style="background:{luz_no};"></div>
                  <div class="bulb" style="background:{luz_si};"></div>
                </div>
                <div>
                  <div class="kpi-big" style="color:{COL['green'] if hay_señal else COL['muted']};">
                    {'SÍ' if hay_señal else 'NO'}</div>
                  <div class="kpi-sub">Desviación vs banda<br>{dev_txt}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # KPI 2 — Basis promedio (Futuro − Spot), últimos 20 días.
    with k2:
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title"><span class="num">2</span>Basis promedio</div>
              <div class="kpi-big" style="color:{COL['orange']};">{basis_prom:,.1f} pts</div>
              <div class="kpi-sub">Promedio últimos 20 días<br>Futuro de mercado − Spot</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # KPI 3 — Días a vencimiento.
    with k3:
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title"><span class="num">3</span>Días a vencimiento</div>
              <div class="kpi-big" style="color:{COL['ink']};">{dias_venc} días</div>
              <div class="kpi-sub">Vencimiento: {fmt_venc(venc_date)}<br>Ciclo trimestral CME</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Tira de métricas del instrumento + acción sugerida ───────────
    m_l, m_r = st.columns([2.6, 1])
    with m_l:
        st.markdown(
            f"""
            <div class="panel">
              <div style="display:flex;justify-content:space-between;">
                <div><div class="metric-lbl">PRECIO SPOT</div>
                     <div class="metric-val" style="color:{COL['teal']};">{spot:,.2f}</div></div>
                <div><div class="metric-lbl">FUTURO DE MERCADO ({ticker})</div>
                     <div class="metric-val" style="color:{COL['orange']};">{F_mkt:,.2f}</div></div>
                <div><div class="metric-lbl">FUTURO TEÓRICO</div>
                     <div class="metric-val" style="color:{COL['green']};">{F_teo:,.2f}</div></div>
                <div><div class="metric-lbl">BASIS</div>
                     <div class="metric-val" style="color:{COL['ink']};">{basis_fs:+,.2f}</div>
                     <div class="metric-note">(F. mercado − Spot)</div></div>
              </div>
              <div style="margin-top:8px;border-top:1px solid {COL['border']};padding-top:6px;
                          display:flex;gap:24px;font-size:0.66rem;">
                <span><span class="metric-lbl">CARRY IMPLÍCITO:</span>
                      <b style="color:{COL['teal']};"> {carry_impl*100:.2f}%</b></span>
                <span><span class="metric-lbl">DESVIACIÓN:</span>
                      <b style="color:{accion_col};"> {desviacion:+.2f} pts ({dir_txt} de la banda)</b></span>
                <span><span class="metric-lbl">MISPRICING:</span>
                      <b style="color:{mispr_col};"> {mispr_lvl} ({mispr:+,.2f})</b></span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m_r:
        st.markdown(
            f"""
            <div class="panel">
              <div class="panel-title">Acción sugerida</div>
              <div class="action" style="background:{accion_col};
                   color:{'#16161B' if accion_col!=COL['muted'] else COL['ink']};">{accion_txt}</div>
              <div class="kpi-sub" style="margin-top:6px;">{accion_nota}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with top_r:
    # Panel de cálculo del futuro teórico (fórmula + inputs + resultado).
    st.markdown(
        f"""
        <div class="panel">
          <div class="panel-title">Cálculo del futuro teórico</div>
          <div style="font-size:1.05rem;text-align:center;margin:6px 0;color:{COL['ink']};">
            F<sub>teórico</sub> = S × e<sup>((r − q + u) × T)</sup></div>
          <div style="font-size:0.66rem;color:{COL['muted']};line-height:1.7;">
            <b style="color:{COL['ink']};">S</b> = precio spot &nbsp;·&nbsp;
            <b style="color:{COL['ink']};">r</b> = tasa libre de riesgo<br>
            <b style="color:{COL['ink']};">q</b> = dividendos &nbsp;·&nbsp;
            <b style="color:{COL['ink']};">u</b> = almacenaje &nbsp;·&nbsp;
            <b style="color:{COL['ink']};">T</b> = tiempo a vencimiento (años)</div>
          <div style="border-top:1px solid {COL['border']};margin:8px 0;padding-top:8px;
                      font-size:0.72rem;color:{COL['teal']};">
            S = {spot:,.2f} &nbsp;|&nbsp; r = {r*100:.2f}% &nbsp;|&nbsp;
            q = {q*100:.2f}% &nbsp;|&nbsp; u = {u*100:.2f}% &nbsp;|&nbsp; T = {dias_venc}/365</div>
          <div style="color:{COL['green']};font-size:0.85rem;font-weight:700;margin-top:6px;">
            Resultado: F<sub>teórico</sub> = {F_teo:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Helper: layout base oscuro para todas las gráficas Plotly ────────
def base_layout(fig, h=250):
    fig.update_layout(
        height=h, margin=dict(l=10, r=10, t=10, b=24),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", size=10, color=COL["muted"]),
        legend=dict(orientation="h", y=1.12, x=1, xanchor="right",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
        hovermode="x unified",
    )
    fig.update_xaxes(gridcolor=COL["grid"], zeroline=False, showline=False)
    fig.update_yaxes(gridcolor=COL["grid"], zeroline=False, showline=False)
    return fig


# ── Bloque 6: Gráficas centrales (convergencia + basis vs banda) ─────
g_l, g_r = st.columns([1.5, 1])

with g_l, st.container(border=True):
    st.markdown('<div class="panel-title">Convergencia del contrato</div>',
                unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["F_mercado"], name="Futuro de Mercado",
                             line=dict(color=COL["orange"], width=2)))
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["F_teorico"], name="Futuro Teórico",
                             line=dict(color=COL["green"], width=2)))
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["spot"], name="Precio Spot",
                             line=dict(color=COL["teal"], width=2)))
    st.plotly_chart(base_layout(fig), use_container_width=True,
                    config={"displayModeBar": False})

with g_r, st.container(border=True):
    st.markdown('<div class="panel-title">Basis en el tiempo vs banda</div>',
                unsafe_allow_html=True)
    fig = go.Figure()
    # Rango normal ±1σ: dos trazas con relleno entre ellas.
    fig.add_trace(go.Scatter(x=d["fecha"], y=[mu + sd] * len(d), name="Rango normal (±1σ)",
                             line=dict(width=0), showlegend=True))
    fig.add_trace(go.Scatter(x=d["fecha"], y=[mu - sd] * len(d), fill="tonexty",
                             fillcolor="rgba(45,212,191,0.10)", line=dict(width=0),
                             showlegend=False, hoverinfo="skip"))
    # Bandas ±2σ punteadas.
    fig.add_hline(y=mu + 2 * sd, line=dict(color=COL["red"], width=1, dash="dash"))
    fig.add_hline(y=mu - 2 * sd, line=dict(color=COL["teal"], width=1, dash="dash"))
    # Línea del basis (Futuro − Spot).
    fig.add_trace(go.Scatter(x=d["fecha"], y=d["basis_fs"], name="Basis (Futuro − Spot)",
                             line=dict(color=COL["orange"], width=2),
                             mode="lines+markers", marker=dict(size=4)))
    # Pastilla con el valor actual.
    fig.add_annotation(x=d["fecha"].iloc[-1], y=basis_fs, text=f"{basis_fs:+.2f}",
                       showarrow=False, font=dict(color="#16161B", size=10),
                       bgcolor=COL["orange"], borderpad=3, xshift=22)
    st.plotly_chart(base_layout(fig), use_container_width=True,
                    config={"displayModeBar": False})


# ── Bloque 7: Histórico (tabla) + proximidad a señal (barras) ────────
b_l, b_r = st.columns([1.5, 1])

with b_l:
    # Construimos la tabla a mano (HTML) para controlar badges y colores.
    filas_html = ""
    for _, rr in d.tail(8).iloc[::-1].iterrows():       # últimos 8, recientes arriba
        s = rr["señal"]
        if s == "VENDE FUTURO":
            btxt, bcol = "SÍ", COL["red"]
        elif s == "COMPRA FUTURO":
            btxt, bcol = "SÍ", COL["green"]
        elif abs(rr["basis"]) >= 0.6 * banda * rr["F_teorico"]:
            btxt, bcol = "CERCA", COL["amber"]          # sin señal, pero cerca
        else:
            btxt, bcol = "NO", COL["muted"]
        bfs = rr["F_mercado"] - rr["spot"]
        col_b = COL["orange"] if bfs >= 0 else COL["teal"]
        filas_html += (
            f"<tr><td class='fecha'>{fmt_fecha(rr['fecha'])}</td>"
            f"<td>{rr['spot']:,.2f}</td><td>{rr['F_mercado']:,.2f}</td>"
            f"<td>{rr['F_teorico']:,.2f}</td>"
            f"<td style='color:{col_b};'>{bfs:+,.2f}</td>"
            f"<td><span class='badge' style='background:{bcol};"
            f"color:{'#16161B' if bcol!=COL['muted'] else COL['ink']};'>{btxt}</span></td></tr>"
        )
    st.markdown(
        f"""
        <div class="panel">
          <div class="panel-title">Histórico del instrumento</div>
          <table class="blotter">
            <tr><th style="text-align:left;">FECHA</th><th>SPOT</th>
                <th>FUT. MERCADO</th><th>FUT. TEÓRICO</th>
                <th>BASIS (pts)</th><th style="text-align:center;">SEÑAL</th></tr>
            {filas_html}
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

with b_r, st.container(border=True):
    st.markdown('<div class="panel-title">Proximidad a señal de arbitraje</div>',
                unsafe_allow_html=True)
    dd = d.tail(10)
    colores = [sigma_color(z) for z in dd["z"]]
    fig = go.Figure(go.Bar(
        x=dd["fecha"], y=dd["basis_fs"], marker_color=colores,
        text=[f"{v:+.1f}" for v in dd["basis_fs"]], textposition="outside",
        textfont=dict(size=9, color=COL["ink"]),
    ))
    # Umbrales de "anomalía" a ambos lados: +2σ (rojo, arriba) y −2σ (teal,
    # abajo). Simétricos: un basis muy negativo es tan raro como uno muy
    # positivo. Sin la línea de abajo, instrumentos con basis negativo
    # (p. ej. el oro) no tendrían referencia visual de cuándo salen del rango.
    fig.add_hline(y=mu + 2 * sd, line=dict(color=COL["red"], width=1, dash="dash"),
                  annotation_text="+2σ", annotation_font=dict(size=8, color=COL["red"]))
    fig.add_hline(y=mu - 2 * sd, line=dict(color=COL["teal"], width=1, dash="dash"),
                  annotation_text="−2σ", annotation_font=dict(size=8, color=COL["teal"]))
    st.plotly_chart(base_layout(fig, h=250), use_container_width=True,
                    config={"displayModeBar": False})


# ── Bloque 8: Barra de estado inferior ───────────────────────────────
n_reg = len(df)
n_instr = len(instrumentos)
st.markdown(
    f"""
    <div class="statusbar">
      <span class="seg"><span class="lbl">FUENTE DE DATOS:</span>
            <b style="color:{COL['green']};"> yfinance (EOD)</b></span>
      <span class="seg"><span class="lbl">ÚLTIMA ACTUALIZACIÓN:</span>
            <b style="color:{COL['ink']};"> {fmt_fecha(hoy)}</b></span>
      <span class="seg"><span class="lbl">FRECUENCIA:</span>
            <b style="color:{COL['ink']};"> Diaria</b></span>
      <span class="seg"><span class="lbl">REGISTROS:</span>
            <b style="color:{COL['ink']};"> {n_reg}</b></span>
      <span class="seg"><span class="lbl">INSTRUMENTOS:</span>
            <b style="color:{COL['ink']};"> {n_instr}</b></span>
      <span class="seg"><span class="lbl">SISTEMA:</span>
            <b style="color:{COL['green']};"> OK</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)
