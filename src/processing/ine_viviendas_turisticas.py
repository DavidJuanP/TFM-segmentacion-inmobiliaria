'''
Procesa las viviendas turísticas municipales del último periodo del INE.

'''
import os
from pathlib import Path

import pandas as pd

try:
    from src.utils.procesamiento_funciones import (
        convertir_numero_es,
        descargar_archivo_s3,
        guardar_parquet,
        separar_municipio_ine,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )
except ModuleNotFoundError:
    from procesamiento_funciones import (
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
S3_KEY_ENTRADA = "ine/viviendas_turisticas.csv"
S3_KEY_SALIDA = "ine_viviendas_turisticas/viviendas_turisticas.parquet"
RUTA_ENTRADA = Path("/tmp/raw/ine/viviendas_turisticas.csv")
RUTA_SALIDA = Path("/tmp/processed/ine/viviendas_turisticas.parquet")
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

    resultado["periodo"] = resultado["Periodo"].str.strip()
    periodo = resultado["periodo"].str.extract(r"^(\d{4})M(\d{2})$")
    resultado["anio"] = pd.to_numeric(periodo[0], errors="coerce")
    resultado["mes"] = pd.to_numeric(periodo[1], errors="coerce")
    periodos_invalidos = resultado["periodo"].notna() & (
        resultado["anio"].isna() | resultado["mes"].isna()
    )
    if periodos_invalidos.any():
        ejemplos = resultado.loc[periodos_invalidos, "periodo"].head(5).tolist()
        raise ValueError(
            f"Hay {periodos_invalidos.sum()} periodos con formato inválido. "
            f"Ejemplos: {ejemplos}"
        )
    if resultado["periodo"].dropna().empty:
        raise ValueError("No hay periodos válidos en viviendas turísticas")

    ultimo_periodo = resultado["periodo"].dropna().max()
    resultado = resultado.loc[resultado["periodo"].eq(ultimo_periodo)].copy()
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
    return resultado[columnas].sort_values("codigo_ine").reset_index(drop=True)


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
    print(f"Periodo conservado: {df_limpio['periodo'].iat[0]}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
