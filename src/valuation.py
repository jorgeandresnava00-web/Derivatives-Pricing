import math


def valuar_futuro(S: float, r: float, q: float, u: float, T: float) -> float:
    """Precio teórico de un futuro usando cost-of-carry: F = S * e^((r - q + u) * T)"""
    return S * math.exp((r - q + u) * T)
