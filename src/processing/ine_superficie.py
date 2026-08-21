'''
Extrae la superficie municipal de los indicadores urbanos del INE.and

'''

from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/ine/superficie.csv")
RUTA_SALIDA = Path("data/processed/ine/superficie.parquet")
COLUMNAS_RAW = {"Municipios", "Indicadores", "Periodo", "Total"}
INDICADOR = "Superficie total (Km2)"


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    mascara = df["Municipios"].notna() & df["Indicadores"].str.strip().eq(INDICADOR)
    resultado = df.loc[mascara, ["Municipios", "Periodo", "Total"]].copy()
    resultado["municipio"] = resultado["Municipios"].str.strip()
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["superficie_km2"] = convertir_numero_es(
        resultado["Total"], "Total"
    )
    resultado = resultado[["municipio", "anio", "superficie_km2"]]
    validar_claves(resultado, ["municipio", "anio"], nombre="superficie municipal")
    resultado["anio"] = resultado["anio"].astype("int16")
    return resultado.sort_values(["municipio", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['municipio'].nunique():,}")
    print(f"Superficies ausentes: {df_limpio['superficie_km2'].isna().sum():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
