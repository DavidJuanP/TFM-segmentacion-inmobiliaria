'''
Limpia el CSV de población municipal del INE y lo guarda en Parquet.

'''

from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    guardar_parquet,
    separar_municipio_ine,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/ine/poblacion.csv")
RUTA_SALIDA = Path("data/processed/ine/poblacion.parquet")
COLUMNAS_RAW = {"Municipios", "Sexo", "Periodo", "Total"}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    # El fichero contiene Total, Hombres y Mujeres. Conservamos exclusivamente la población total.
    resultado = df.loc[
        df["Sexo"].str.strip().str.casefold().eq("total"),
        ["Municipios", "Periodo", "Total"],
    ].copy()

    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(resultado["Municipios"])
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["poblacion"] = convertir_numero_es(resultado["Total"], "Total", entero=True)

    columnas = ["codigo_ine", "municipio", "anio", "poblacion"]
    resultado = resultado[columnas]
    validar_claves(
        resultado,
        ["codigo_ine", "anio"],
        nombre="población municipal",
    )
    resultado["anio"] = resultado["anio"].astype("int16")
    return resultado.sort_values(["codigo_ine", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Poblaciones ausentes: {df_limpio['poblacion'].isna().sum():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
