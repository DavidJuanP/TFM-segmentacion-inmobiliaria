'''
Normaliza los hechos de okupación por comunidad autónoma y año del MIR.

'''

import os
from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    descargar_archivo_s3,
    guardar_parquet,
    subir_archivo_s3,
    validar_claves,
    validar_columnas,
)


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "mir/okupacion.csv"
S3_KEY_SALIDA = "mir/okupacion.parquet"
RUTA_ENTRADA = Path("/tmp/raw/mir/okupacion.csv")
RUTA_SALIDA = Path("/tmp/processed/mir/okupacion.parquet")
COLUMNAS_RAW = {"Comunidades autónomas", "periodo", "Total"}
GEOGRAFIAS_EXCLUIDAS = {
    "TOTAL NACIONAL",
    "DESCONOCIDA",
    "EN EL EXTRANJERO",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    resultado = df[["Comunidades autónomas", "periodo", "Total"]].copy()
    resultado["comunidad"] = resultado["Comunidades autónomas"].str.strip()
    resultado = resultado.loc[
        resultado["comunidad"].notna()
        & resultado["comunidad"].ne("")
        & ~resultado["comunidad"].isin(GEOGRAFIAS_EXCLUIDAS)
    ].copy()
    resultado["anio"] = pd.to_numeric(resultado["periodo"], errors="coerce")
    resultado["total_okupaciones"] = convertir_numero_es(
        resultado["Total"], "Total", entero=True
    )

    resultado = resultado[["comunidad", "anio", "total_okupaciones"]]
    validar_claves(
        resultado,
        ["comunidad", "anio"],
        nombre="okupación por comunidad autónoma",
    )
    resultado["anio"] = resultado["anio"].astype("int16")
    return resultado.sort_values(["comunidad", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ENTRADA, RUTA_ENTRADA)
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    salida_s3 = subir_archivo_s3(
        RUTA_SALIDA, PROCESSED_BUCKET, S3_KEY_SALIDA
    )
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Comunidades: {df_limpio['comunidad'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(
        "Totales ausentes: "
        f"{df_limpio['total_okupaciones'].isna().sum():,}"
    )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
