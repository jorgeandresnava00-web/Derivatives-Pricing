from datetime import date

import yfinance as yf
import pandas as pd


def _solo_cerradas(datos: pd.DataFrame) -> pd.DataFrame:
    """Quita el bar del día en curso (intraday, aún sin cerrar).

    yfinance, si el mercado está abierto, agrega una fila con la fecha de HOY
    cuyo 'Close' es el último precio en vivo, NO el cierre EOD. Tomar ese valor
    contamina el histórico con un precio que cambiará al cierre. Aquí dejamos
    solo las sesiones ya cerradas (fecha < hoy). El fallback (devolver todo si
    no quedara nada) cubre el caso límite improbable de que solo haya intraday.
    """
    hoy = date.today()
    cerradas = datos[datos.index.date < hoy]
    return cerradas if not cerradas.empty else datos


def precio_cierre(ticker: str) -> float:
    """Devuelve el último precio de cierre EOD COMPLETADO del ticker.

    Ignora el bar intraday de hoy: el precio sale de la misma sesión que
    fecha_ultimo_cierre, así fecha y precio nunca quedan descalibrados.
    """
    datos = _solo_cerradas(yf.Ticker(ticker).history(period="5d"))
    return float(datos["Close"].iloc[-1])


def fecha_ultimo_cierre(ticker: str = "^GSPC") -> str:
    """Fecha del último cierre EOD completado, en formato ISO (YYYY-MM-DD).

    Usa el mismo filtro que precio_cierre, así la fecha etiquetada y los
    precios guardados provienen siempre de la misma sesión cerrada.
    """
    datos = _solo_cerradas(yf.Ticker(ticker).history(period="5d"))
    return datos.index[-1].date().isoformat()


def precio_spot(ticker: str, factor: float) -> float:
    """Precio spot del subyacente, escalado por 'factor'.

    Para el S&P, '^GSPC' es spot real y factor=1.0.
    Para metales, yfinance ya no da spot directo: usamos un ETF
    (GLD, SLV) multiplicado por un factor que lo lleva a la escala
    del futuro. Reutiliza precio_cierre — la lógica de jalar el
    precio ya existe, aquí solo la escalamos.
    """
    return precio_cierre(ticker) * factor


def tasa_libre_riesgo() -> float:
    """Devuelve la tasa ^IRX (último cierre EOD) como decimal (ej. 5.2% → 0.052)."""
    datos = _solo_cerradas(yf.Ticker("^IRX").history(period="5d"))
    return float(datos["Close"].iloc[-1]) / 100


# ── Versiones "serie" para el backfill ───────────────────────────────
# Las de arriba devuelven un solo número (el de HOY, vía .iloc[-1]) y las
# usa run.py. Las de abajo conservan la COLUMNA ENTERA indexada por fecha
# — varios días — que es lo que el backfill necesita para rebobinar.

def serie_cierre(ticker: str, periodo: str = "1mo") -> pd.Series:
    """Serie diaria de cierres EOD del ticker, indexada por fecha (date).

    Descarta el bar intraday de hoy: el backfill solo debe ver sesiones
    cerradas, igual que run.py.
    """
    datos = _solo_cerradas(yf.Ticker(ticker).history(period=periodo))
    serie = datos["Close"]
    serie.index = serie.index.date   # Timestamp con zona horaria → date simple, para alinear por día
    return serie


def serie_spot(ticker: str, factor: float, periodo: str = "1mo") -> pd.Series:
    """Serie diaria del spot del subyacente, escalada por 'factor'. Reusa serie_cierre."""
    return serie_cierre(ticker, periodo) * factor


def serie_tasa(periodo: str = "1mo") -> pd.Series:
    """Serie diaria de la tasa ^IRX como decimal, indexada por fecha."""
    return serie_cierre("^IRX", periodo) / 100
