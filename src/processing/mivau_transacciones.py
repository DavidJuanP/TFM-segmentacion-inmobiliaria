'''
Normaliza las transacciones inmobiliarias provinciales del MIVAU.

'''
from pathlib import Path

import pandas as pd

from src.processing._common import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/mivau/transacciones.csv")
RUTA_SALIDA = Path("data/processed/mivau/transacciones.parquet")
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
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Provincias: {df_limpio['codigo_provincia'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
