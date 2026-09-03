'''
Limpia los saldos migratorios municipales del INE.
'''

import os
from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    descargar_archivo_s3,
    guardar_parquet,
    separar_municipio_ine,
    subir_archivo_s3,
    validar_claves,
    validar_columnas,
)


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "ine/migracion.csv"
S3_KEY_SALIDA = "ine/migracion.parquet"
RUTA_ENTRADA = Path("/tmp/raw/ine/migracion.csv")
RUTA_SALIDA = Path("/tmp/processed/ine/migracion.parquet")
COLUMNAS_RAW = {"Municipios", "Sexo", "Tipo de saldo", "Periodo", "Total"}
TIPOS_SALDO = {
    "Saldo total": "saldo_total",
    "Saldo interior": "saldo_interior",
    "Saldo exterior": "saldo_exterior",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    mascara = df["Municipios"].notna() & df["Sexo"].str.strip().str.casefold().eq(
        "ambos sexos"
    )
    resultado = df.loc[
        mascara, ["Municipios", "Tipo de saldo", "Periodo", "Total"]
    ].copy()
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["tipo_saldo"] = resultado["Tipo de saldo"].map(TIPOS_SALDO)
    resultado["saldo"] = convertir_numero_es(resultado["Total"], "Total", entero=True)
    validar_claves(
        resultado,
        ["codigo_ine", "anio", "tipo_saldo"],
        nombre="saldos migratorios",
    )

    resultado = resultado.pivot(
        index=["codigo_ine", "municipio", "anio"],
        columns="tipo_saldo",
        values="saldo",
    ).reset_index()
    resultado.columns.name = None
    for columna in TIPOS_SALDO.values():
        if columna not in resultado:
            resultado[columna] = pd.NA
        resultado[columna] = resultado[columna].astype("Int64")
    resultado["anio"] = resultado["anio"].astype("int16")

    columnas = ["codigo_ine", "municipio", "anio", *TIPOS_SALDO.values()]
    return resultado[columnas].sort_values(["codigo_ine", "anio"]).reset_index(
        drop=True
    )


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
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
