import yaml
from datetime import date
from src.data import precio_cierre, precio_spot, tasa_libre_riesgo
from src.maturity import tiempo_a_vencimiento
from src.valuation import valuar_futuro
from src.arbitrage import calcular_basis, señal_arbitraje
from src.storage import guardar_registro

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

r = tasa_libre_riesgo()
T = tiempo_a_vencimiento()
hoy = date.today().isoformat()

for ticker, params in cfg["instrumentos"].items():
    S         = precio_spot(params["spot"], params["factor"])
    F_mercado = precio_cierre(ticker)
    q         = params["q"]
    u         = params["u"]

    F_teorico = valuar_futuro(S, r, q, u, T)
    basis     = calcular_basis(F_mercado, F_teorico)
    banda_usd = F_teorico * cfg["banda_costos"]
    señal     = señal_arbitraje(basis, banda_usd)

    registro = {
        "fecha":      hoy,
        "ticker":     ticker,
        "r":          round(r, 5),   # tasa libre de riesgo de ese día
        "T":          round(T, 5),   # años al vencimiento de ese día
        "spot":       round(S, 2),
        "F_mercado":  round(F_mercado, 2),
        "F_teorico":  round(F_teorico, 2),
        "basis":      round(basis, 2),
        "señal":      señal,
    }

    guardar_registro(cfg["ruta_csv"], registro)
    print(f"{ticker}: F_mercado={F_mercado:.2f} | F_teorico={F_teorico:.2f} | basis={basis:.2f} | {señal}")
