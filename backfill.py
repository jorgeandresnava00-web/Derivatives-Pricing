"""Backfill de histórico — rebobina las últimas ~semanas y valúa cada día
como si hubiéramos corrido el pipeline ese día.

Gemelo de run.py: misma valuación, mismos módulos. La única diferencia es
que run.py procesa SOLO hoy (.iloc[-1]) y este procesa la SERIE completa,
recalculando T para cada fecha. No toca valuation/arbitrage/storage:
la separación de responsabilidades permite reusarlos tal cual.

Uso:  python backfill.py
"""
import yaml
import pandas as pd

from src.data import serie_spot, serie_cierre, serie_tasa
from src.maturity import proximo_vencimiento
from src.valuation import valuar_futuro
from src.arbitrage import calcular_basis, señal_arbitraje
from src.storage import guardar_registro, cargar_historico

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

tasas = serie_tasa()                 # r por fecha (^IRX), se jala una sola vez

# Fechas ya guardadas → para no pisar la corrida real de run.py ni duplicar
hist = cargar_historico(cfg["ruta_csv"])
ya_existe = set(zip(hist["fecha"], hist["ticker"])) if not hist.empty else set()

filas_nuevas = 0
for ticker, params in cfg["instrumentos"].items():
    futuros = serie_cierre(ticker)                          # serie del futuro
    spots   = serie_spot(params["spot"], params["factor"])  # serie del spot real
    q, u    = params["q"], params["u"]

    # ALINEAR las tres series por fecha. El DataFrame las junta por índice
    # (fecha); dropna() deja solo los días que tienen spot Y futuro Y r.
    df = pd.DataFrame({"spot": spots, "F_mercado": futuros, "r": tasas}).dropna()

    for fecha, fila in df.iterrows():
        if (fecha.isoformat(), ticker) in ya_existe:
            continue                                         # ese día ya está en el CSV

        # El vencimiento que tocaba ESE día (no el de hoy): protege el rollover.
        # Un día de mayo → junio; un día de julio → septiembre.
        venc = proximo_vencimiento(desde=fecha)
        T    = (venc - fecha).days / 365.0

        S         = float(fila["spot"])
        F_mercado = float(fila["F_mercado"])
        r         = float(fila["r"])

        F_teorico = valuar_futuro(S, r, q, u, T)
        basis     = calcular_basis(F_mercado, F_teorico)
        banda_usd = F_teorico * cfg["banda_costos"]
        señal     = señal_arbitraje(basis, banda_usd)

        registro = {
            "fecha":     fecha.isoformat(),
            "ticker":    ticker,
            "r":         round(r, 5),
            "T":         round(T, 5),
            "spot":      round(S, 2),
            "F_mercado": round(F_mercado, 2),
            "F_teorico": round(F_teorico, 2),
            "basis":     round(basis, 2),
            "señal":     señal,
        }
        guardar_registro(cfg["ruta_csv"], registro)
        filas_nuevas += 1
        print(f"{fecha} {ticker}: spot={S:.2f} | F_mer={F_mercado:.2f} | F_teo={F_teorico:.2f} | basis={basis:.2f} | {señal}")

print(f"\nBackfill terminado: {filas_nuevas} filas nuevas agregadas a {cfg['ruta_csv']}")
