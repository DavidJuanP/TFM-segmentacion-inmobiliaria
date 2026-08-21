'''
Normaliza los indicadores municipales de alquiler del MIVAU.

'''

from pathlib import Path

import pandas as pd

from src.processing._common import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/mivau/alquiler.csv")
RUTA_SALIDA = Path("data/processed/mivau/alquiler.parquet")
COLUMNAS_RAW = {
    "COD_PROVINCIA",
    "PROVINCIA",
    "COD_POSTAL",
    "NOMBRE_MUNICIPIO",
    "ELEMENTO",
    "TIPO_VIVIENDA",
    "TIPO_MEDIDA",
    "AÑO",
    "VALOR",
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
            "COD_PROVINCIA": "codigo_provincia",
            "PROVINCIA": "provincia",
            # Aunque el origen lo llama COD_POSTAL, contiene el código INE.
            "COD_POSTAL": "codigo_ine",
            "NOMBRE_MUNICIPIO": "municipio",
            "ELEMENTO": "elemento",
            "TIPO_VIVIENDA": "tipo_vivienda",
            "TIPO_MEDIDA": "tipo_medida",
            "AÑO": "anio",
            "VALOR": "valor",
        }
    )
    resultado["codigo_provincia"] = (
        resultado["codigo_provincia"].str.strip().str.zfill(2)
    )
    resultado["codigo_ine"] = resultado["codigo_ine"].str.strip().str.zfill(5)
    for columna in [
        "provincia",
        "municipio",
        "elemento",
        "tipo_vivienda",
        "tipo_medida",
    ]:
        resultado[columna] = resultado[columna].str.strip()
    resultado["anio"] = pd.to_numeric(resultado["anio"], errors="coerce")
    resultado["valor"] = convertir_numero_es(
        resultado["valor"], "VALOR", decimal_coma=False
    )

    claves = [
        "codigo_ine",
        "anio",
        "elemento",
        "tipo_vivienda",
        "tipo_medida",
    ]
    validar_claves(resultado, claves, nombre="indicadores de alquiler")
    resultado["anio"] = resultado["anio"].astype("int16")
    columnas = [
        "codigo_ine",
        "municipio",
        "codigo_provincia",
        "provincia",
        "anio",
        "tipo_vivienda",
        "elemento",
        "tipo_medida",
        "valor",
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
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Valores ausentes: {df_limpio['valor'].isna().sum():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
