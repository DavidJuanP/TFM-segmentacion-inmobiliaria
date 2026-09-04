'''
Calcula la población de 2025 y sus variaciones municipales a 1, 3 y 5 años.

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
S3_KEY_ENTRADA = "ine/poblacion.csv"
S3_KEY_SALIDA = "ine/poblacion.parquet"
RUTA_ENTRADA = Path("/tmp/raw/ine/poblacion.csv")
RUTA_SALIDA = Path("/tmp/processed/ine/poblacion.parquet")
COLUMNAS_RAW = {"Municipios", "Sexo", "Periodo", "Total"}
ANIO_REFERENCIA = 2025
HORIZONTES = {
    1: 2024,
    3: 2022,
    5: 2020,
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    # El fichero contiene Total, Hombres y Mujeres. Conservamos exclusivamente
    # la población total de los años necesarios para calcular las variaciones.
    resultado = df.loc[
        df["Sexo"].str.strip().str.casefold().eq("total"),
        ["Municipios", "Periodo", "Total"],
    ].copy()

    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["poblacion"] = convertir_numero_es(
        resultado["Total"], "Total", entero=True
    )

    columnas = ["codigo_ine", "municipio", "anio", "poblacion"]
    resultado = resultado[columnas]
    validar_claves(
        resultado,
        ["codigo_ine", "anio"],
        nombre="población municipal",
    )
    resultado["anio"] = resultado["anio"].astype("int16")

    anios_necesarios = {ANIO_REFERENCIA, *HORIZONTES.values()}
    anios_ausentes = anios_necesarios.difference(resultado["anio"].unique())
    if anios_ausentes:
        raise ValueError(
            f"Faltan años necesarios para calcular las variaciones: "
            f"{sorted(anios_ausentes)}"
        )

    poblacion_referencia = resultado.loc[
        resultado["anio"].eq(ANIO_REFERENCIA),
        ["codigo_ine", "municipio", "poblacion"],
    ].rename(columns={"poblacion": "poblacion_2025"})
    validar_claves(
        poblacion_referencia,
        ["codigo_ine"],
        nombre=f"población municipal de {ANIO_REFERENCIA}",
    )

    for numero_anios, anio_anterior in HORIZONTES.items():
        columna_anterior = f"poblacion_{anio_anterior}"
        columna_variacion = (
            f"variacion_poblacion_{numero_anios}_anio"
            if numero_anios == 1
            else f"variacion_poblacion_{numero_anios}_anios"
        )
        poblacion_anterior = resultado.loc[
            resultado["anio"].eq(anio_anterior),
            ["codigo_ine", "poblacion"],
        ].rename(columns={"poblacion": columna_anterior})
        poblacion_referencia = poblacion_referencia.merge(
            poblacion_anterior,
            on="codigo_ine",
            how="left",
            validate="one_to_one",
        )
        poblacion_referencia[columna_variacion] = (
            poblacion_referencia["poblacion_2025"]
            - poblacion_referencia.pop(columna_anterior)
        ).astype("Int64")

    columnas_salida = [
        "codigo_ine",
        "municipio",
        "poblacion_2025",
        "variacion_poblacion_1_anio",
        "variacion_poblacion_3_anios",
        "variacion_poblacion_5_anios",
    ]
    return poblacion_referencia[columnas_salida].sort_values(
        "codigo_ine"
    ).reset_index(drop=True)


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
    print(f"Año de referencia: {ANIO_REFERENCIA}")
    print(f"Poblaciones de 2025 ausentes: {df_limpio['poblacion_2025'].isna().sum():,}")
    for numero_anios in HORIZONTES:
        sufijo = "anio" if numero_anios == 1 else "anios"
        columna = f"variacion_poblacion_{numero_anios}_{sufijo}"
        print(
            f"Variaciones a {numero_anios} año(s) ausentes: "
            f"{df_limpio[columna].isna().sum():,}"
        )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
