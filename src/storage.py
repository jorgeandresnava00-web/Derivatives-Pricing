import pandas as pd
from pathlib import Path


def guardar_registro(ruta: str, registro: dict) -> None:
    """Agrega una fila nueva al CSV histórico. Lo crea si no existe."""
    ruta = Path(ruta)
    nueva_fila = pd.DataFrame([registro])

    if ruta.exists():
        df_existente = pd.read_csv(ruta)
        ya_existe = (
            (df_existente["fecha"] == registro["fecha"]) &
            (df_existente["ticker"] == registro["ticker"])
        ).any()
        if ya_existe:
            return
        df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
    else:
        df_actualizado = nueva_fila

    df_actualizado.to_csv(ruta, index=False)


def cargar_historico(ruta: str) -> pd.DataFrame:
    """Lee el CSV histórico completo. Devuelve DataFrame vacío si no existe."""
    ruta = Path(ruta)
    if ruta.exists():
        return pd.read_csv(ruta)
    return pd.DataFrame()
