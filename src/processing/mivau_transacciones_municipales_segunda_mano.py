'''
Calcula las transacciones municipales de vivienda de segunda mano de 2025 y
sus diferencias absolutas a 1, 3 y 5 años.

'''

import os
from pathlib import Path

import pandas as pd

try:
    from src.processing.mivau_transacciones_municipales import (
        ANIO_REFERENCIA,
        HORIZONTES,
        leer_alias_municipios,
        leer_catalogo_municipios,
        leer_datos as leer_datos_base,
        procesar_datos as procesar_datos_base,
    )
except ModuleNotFoundError:
    from mivau_transacciones_municipales import (
        ANIO_REFERENCIA,
        HORIZONTES,
        leer_alias_municipios,
        leer_catalogo_municipios,
        leer_datos as leer_datos_base,
        procesar_datos as procesar_datos_base,
    )

try:
    from src.utils.procesamiento_funciones import (
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
    )
except ModuleNotFoundError:
    from procesamiento_funciones import (
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
    )


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "mivau/transacciones_segunda_mano.xls"
S3_KEY_CATALOGO = "ign/municipios.xlsx"
S3_KEY_ALIAS = "mivau/alquiler.csv"
S3_KEY_SALIDA = "mivau_transacciones_segunda_mano/transacciones_segunda_mano.parquet"
RUTA_ENTRADA = Path("/tmp/raw/mivau/transacciones_segunda_mano.xls")
RUTA_CATALOGO = Path("/tmp/raw/ign/municipios.xlsx")
RUTA_ALIAS = Path("/tmp/raw/mivau/alquiler.csv")
RUTA_SALIDA = Path(
    "/tmp/processed/mivau/transacciones_segunda_mano.parquet"
)

COLUMNAS_TRANSACCIONES = {
    "transacciones_2025": "transacciones_segunda_mano_2025",
    "diferencia_transacciones_1_anio": (
        "diferencia_transacciones_segunda_mano_1_anio"
    ),
    "diferencia_transacciones_3_anios": (
        "diferencia_transacciones_segunda_mano_3_anios"
    ),
    "diferencia_transacciones_5_anios": (
        "diferencia_transacciones_segunda_mano_5_anios"
    ),
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    return leer_datos_base(ruta)


def procesar_datos(
    df: pd.DataFrame,
    catalogo_municipios: pd.DataFrame,
    alias_municipios: pd.DataFrame,
) -> pd.DataFrame:
    resultado = procesar_datos_base(
        df,
        catalogo_municipios,
        alias_municipios,
    )
    return resultado.rename(columns=COLUMNAS_TRANSACCIONES)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ENTRADA, RUTA_ENTRADA)
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_CATALOGO, RUTA_CATALOGO)
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ALIAS, RUTA_ALIAS)
    df_raw = leer_datos()
    catalogo = leer_catalogo_municipios(RUTA_CATALOGO)
    aliases = leer_alias_municipios(RUTA_ALIAS)
    df_limpio = procesar_datos(df_raw, catalogo, aliases)
    guardar_datos(df_limpio)
    salida_s3 = subir_archivo_s3(
        RUTA_SALIDA, PROCESSED_BUCKET, S3_KEY_SALIDA
    )
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Año de referencia: {ANIO_REFERENCIA}")
    print(
        "Transacciones de segunda mano de 2025 ausentes: "
        f"{df_limpio['transacciones_segunda_mano_2025'].isna().sum():,}"
    )
    for numero_anios in HORIZONTES:
        sufijo = "anio" if numero_anios == 1 else "anios"
        columna = (
            f"diferencia_transacciones_segunda_mano_{numero_anios}_{sufijo}"
        )
        print(
            f"Diferencias a {numero_anios} año(s) ausentes: "
            f"{df_limpio[columna].isna().sum():,}"
        )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
