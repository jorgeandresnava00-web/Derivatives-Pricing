import yfinance as yf
import pandas as pd


def precio_cierre(ticker: str) -> float:
    """Devuelve el último precio de cierre EOD disponible para el ticker."""
    datos = yf.Ticker(ticker).history(period="5d")
    return float(datos["Close"].iloc[-1])


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
    """Devuelve la tasa ^IRX como decimal (ej. 5.2% → 0.052)."""
    datos = yf.Ticker("^IRX").history(period="5d")
    return float(datos["Close"].iloc[-1]) / 100


# ── Versiones "serie" para el backfill ───────────────────────────────
# Las de arriba devuelven un solo número (el de HOY, vía .iloc[-1]) y las
# usa run.py. Las de abajo conservan la COLUMNA ENTERA indexada por fecha
# — varios días — que es lo que el backfill necesita para rebobinar.

def serie_cierre(ticker: str, periodo: str = "1mo") -> pd.Series:
    """Serie diaria de cierres EOD del ticker, indexada por fecha (date)."""
    datos = yf.Ticker(ticker).history(period=periodo)
    serie = datos["Close"]
    serie.index = serie.index.date   # Timestamp con zona horaria → date simple, para alinear por día
    return serie


def serie_spot(ticker: str, factor: float, periodo: str = "1mo") -> pd.Series:
    """Serie diaria del spot del subyacente, escalada por 'factor'. Reusa serie_cierre."""
    return serie_cierre(ticker, periodo) * factor


def serie_tasa(periodo: str = "1mo") -> pd.Series:
    """Serie diaria de la tasa ^IRX como decimal, indexada por fecha."""
    return serie_cierre("^IRX", periodo) / 100
