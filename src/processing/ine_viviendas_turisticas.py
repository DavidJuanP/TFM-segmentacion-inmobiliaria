"""Limpia las viviendas turísticas municipales publicadas por el INE."""

from pathlib import Path

import pandas as pd

from src.processing._common import (
    convertir_numero_es,
    guardar_parquet,
    separar_municipio_ine,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/ine/viviendas_turisticas.csv")
RUTA_SALIDA = Path("data/processed/ine/viviendas_turisticas.parquet")
COLUMNAS_RAW = {"Municipios", "Viviendas y plazas", "Periodo", "Total"}
METRICAS = {
    "Viviendas turísticas": "viviendas_turisticas",
    "Plazas": "plazas",
    "Plazas por vivienda turística": "plazas_por_vivienda",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.loc[
        df["Municipios"].notna(),
        ["Municipios", "Viviendas y plazas", "Periodo", "Total"],
    ].copy()
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["metrica"] = resultado["Viviendas y plazas"].map(METRICAS)
    resultado["valor"] = convertir_numero_es(resultado["Total"], "Total")

    periodo = resultado["Periodo"].str.extract(r"^(\d{4})M(\d{2})$")
    resultado["anio"] = pd.to_numeric(periodo[0], errors="coerce")
    resultado["mes"] = pd.to_numeric(periodo[1], errors="coerce")
    resultado["periodo"] = resultado["Periodo"].str.strip()
    validar_claves(
        resultado,
        ["codigo_ine", "periodo", "metrica"],
        nombre="viviendas turísticas",
    )

    resultado = resultado.pivot(
        index=["codigo_ine", "municipio", "periodo", "anio", "mes"],
        columns="metrica",
        values="valor",
    ).reset_index()
    resultado.columns.name = None
    for columna in METRICAS.values():
        if columna not in resultado:
            resultado[columna] = pd.NA
    for columna in ["viviendas_turisticas", "plazas"]:
        resultado[columna] = resultado[columna].astype("Int64")
    resultado["plazas_por_vivienda"] = resultado["plazas_por_vivienda"].astype(
        "Float64"
    )
    resultado = resultado.astype({"anio": "int16", "mes": "int8"})

    columnas = [
        "codigo_ine",
        "municipio",
        "periodo",
        "anio",
        "mes",
        *METRICAS.values(),
    ]
    return resultado[columnas].sort_values(
        ["codigo_ine", "anio", "mes"]
    ).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Periodos: {df_limpio['periodo'].nunique():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
