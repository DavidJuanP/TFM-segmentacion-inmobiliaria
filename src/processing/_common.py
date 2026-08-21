"""Utilidades compartidas por los procesos de limpieza."""

from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd


def validar_columnas(df: pd.DataFrame, columnas: Iterable[str]) -> None:
    """Comprueba que el origen contiene todas las columnas esperadas."""
    faltantes = set(columnas).difference(df.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas: {sorted(faltantes)}. "
            f"Disponibles: {df.columns.tolist()}"
        )


def convertir_numero_es(
    serie: pd.Series,
    nombre: str,
    *,
    entero: bool = False,
    nulos_adicionales: Iterable[str] = (),
    decimal_coma: bool = True,
) -> pd.Series:
    """Convierte números localizados sin imputar sus valores ausentes."""
    texto = serie.astype("string").str.strip()
    marcadores_nulos = {"", "..", *nulos_adicionales}
    texto = texto.mask(texto.isin(marcadores_nulos))
    if decimal_coma:
        normalizado = texto.str.replace(".", "", regex=False).str.replace(
            ",", ".", regex=False
        )
    else:
        normalizado = texto
    numero = pd.to_numeric(normalizado, errors="coerce")

    invalidos = texto.notna() & numero.isna()
    if invalidos.any():
        ejemplos = serie.loc[invalidos].head(5).tolist()
        raise ValueError(
            f"Hay {invalidos.sum()} valores no numéricos en {nombre}. "
            f"Ejemplos: {ejemplos}"
        )

    if entero:
        no_enteros = numero.notna() & numero.mod(1).ne(0)
        if no_enteros.any():
            ejemplos = serie.loc[no_enteros].head(5).tolist()
            raise ValueError(
                f"Hay {no_enteros.sum()} valores no enteros en {nombre}. "
                f"Ejemplos: {ejemplos}"
            )
        return numero.astype("Int64")

    return numero.astype("Float64")


def separar_municipio_ine(serie: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Separa una etiqueta del INE con formato ``12345 Nombre``."""
    texto = serie.astype("string").str.strip()
    codigo = texto.str.extract(r"^(\d{5})\s+", expand=False).str.zfill(5)
    municipio = texto.str.replace(r"^\d{5}\s+", "", regex=True).str.strip()
    municipio = municipio.mask(municipio.eq(""))
    return codigo, municipio


def validar_claves(
    df: pd.DataFrame, claves: Sequence[str], *, nombre: str = "resultado"
) -> None:
    """Valida que una clave esté completa y sea única."""
    incompletas = df[list(claves)].isna().any(axis=1)
    if incompletas.any():
        ejemplos = df.loc[incompletas, list(claves)].head(5).to_dict("records")
        raise ValueError(
            f"Hay {incompletas.sum()} claves incompletas en {nombre}. "
            f"Ejemplos: {ejemplos}"
        )

    duplicadas = df.duplicated(subset=list(claves), keep=False)
    if duplicadas.any():
        ejemplos = df.loc[duplicadas, list(claves)].head(5).to_dict("records")
        raise ValueError(
            f"La clave {list(claves)} no es única en {nombre}. "
            f"Ejemplos: {ejemplos}"
        )


def guardar_parquet(df: pd.DataFrame, ruta: Path) -> None:
    """Crea el directorio de destino y escribe un Parquet Zstandard."""
    destino = Path(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(
        destino, index=False, engine="pyarrow", compression="zstd"
    )
