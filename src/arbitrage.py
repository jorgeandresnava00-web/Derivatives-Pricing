def calcular_basis(F_mercado: float, F_teorico: float) -> float:
    """Diferencia entre el precio de mercado y el teórico: basis = F_mercado - F_teórico"""
    return F_mercado - F_teorico


def señal_arbitraje(basis: float, banda: float) -> str:
    """Devuelve la señal de arbitraje según la magnitud del basis."""
    if basis > banda:
        return "VENDE FUTURO"
    if basis < -banda:
        return "COMPRA FUTURO"
    return "SIN SEÑAL"
