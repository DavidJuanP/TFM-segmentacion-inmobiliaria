'''
Normaliza las transacciones inmobiliarias provinciales del MIVAU.

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
S3_KEY_ENTRADA = "mivau/transacciones.csv"
S3_KEY_SALIDA = "mivau/transacciones.parquet"
RUTA_ENTRADA = Path("/tmp/raw/mivau/transacciones.csv")
RUTA_SALIDA = Path("/tmp/processed/mivau/transacciones.parquet")
COLUMNAS_RAW = {
    "CODCOMUNIDAD",
    "COMUNIDAD",
    "CODPROVINCIA",
    "PROVINCIA",
    "Tipo",
    "Año",
    "Trimestre",
    "Numero_Transacciones",
    "Valor_Transacciones",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df[list(COLUMNAS_RAW)].copy().rename(
        columns={
            "CODCOMUNIDAD": "codigo_comunidad",
            "COMUNIDAD": "comunidad",
            "CODPROVINCIA": "codigo_provincia",
            "PROVINCIA": "provincia",
            "Tipo": "tipo_vivienda",
            "Año": "anio",
            "Trimestre": "trimestre",
            "Numero_Transacciones": "numero_transacciones",
            "Valor_Transacciones": "valor_transacciones_eur",
        }
    )
    resultado["codigo_comunidad"] = (
        resultado["codigo_comunidad"].str.strip().str.zfill(2)
    )
    resultado["codigo_provincia"] = (
        resultado["codigo_provincia"].str.strip().str.zfill(2)
    )
    for columna in ["comunidad", "provincia", "tipo_vivienda"]:
        resultado[columna] = resultado[columna].str.strip()
    resultado["anio"] = pd.to_numeric(resultado["anio"], errors="coerce")
    resultado["trimestre"] = pd.to_numeric(
        resultado["trimestre"], errors="coerce"
    )
    resultado["numero_transacciones"] = convertir_numero_es(
        resultado["numero_transacciones"],
        "Numero_Transacciones",
        entero=True,
        decimal_coma=False,
    )
    resultado["valor_transacciones_eur"] = convertir_numero_es(
        resultado["valor_transacciones_eur"],
        "Valor_Transacciones",
        decimal_coma=False,
    )

    claves = ["codigo_provincia", "anio", "trimestre", "tipo_vivienda"]
    validar_claves(resultado, claves, nombre="transacciones provinciales")
    resultado = resultado.astype({"anio": "int16", "trimestre": "int8"})
    columnas = [
        "codigo_comunidad",
        "comunidad",
        "codigo_provincia",
        "provincia",
        "anio",
        "trimestre",
        "tipo_vivienda",
        "numero_transacciones",
        "valor_transacciones_eur",
    ]
    return resultado[columnas].sort_values(claves).reset_index(drop=True)


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
    print(f"Provincias: {df_limpio['codigo_provincia'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
