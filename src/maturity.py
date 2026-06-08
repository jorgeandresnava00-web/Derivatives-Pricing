from datetime import date, timedelta

MESES_TRIMESTRALES = {3, 6, 9, 12}


def _tercer_viernes(year: int, month: int) -> date:
    """Devuelve el tercer viernes del mes — regla CME para futuros de equity e índices."""
    primer_dia = date(year, month, 1)
    dia_semana = primer_dia.weekday()        # 0=Lun … 4=Vie
    dias_hasta_viernes = (4 - dia_semana) % 7
    primer_viernes = primer_dia + timedelta(days=dias_hasta_viernes)
    return primer_viernes + timedelta(weeks=2)


def proximo_vencimiento(desde: date = None) -> date:
    """Próximo vencimiento trimestral CME (ciclo Mar/Jun/Sep/Dic), 3er viernes del mes.

    Por defecto mide desde HOY (lo que usa run.py). El backfill le pasa
    'desde=fecha' para obtener el vencimiento que tocaba ESE día histórico,
    no el de hoy — así no le asigna a un día de junio el vencimiento de septiembre.
    """
    hoy = desde or date.today()
    for y in [hoy.year, hoy.year + 1]:
        for m in [3, 6, 9, 12]:
            venc = _tercer_viernes(y, m)
            if venc > hoy:
                return venc
    raise RuntimeError("No se encontró vencimiento trimestral")  # nunca debería llegar aquí


def tiempo_a_vencimiento() -> float:
    """T en años: días hasta el próximo vencimiento trimestral / 365."""
    hoy = date.today()
    venc = proximo_vencimiento()
    return (venc - hoy).days / 365.0
