'''
Extrae el total anual de infracciones penales por municipio del MIR.

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


RUTA_ENTRADA = Path("data/raw/mir/criminalidad.csv")
RUTA_SALIDA = Path("data/processed/mir/criminalidad.parquet")
COLUMNAS_RAW = {"Geografía", "Tipología penal", "Periodos:", "Total"}
TIPOLOGIA_TOTAL = "III. TOTAL INFRACCIONES PENALES"


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    periodo = df["Periodos:"].str.extract(
        r"^enero-diciembre\s+(\d{4})$", expand=False
    )
    mascara = (
        df["Geografía"].str.match(r"^\d{5}\s+", na=False)
        & df["Tipología penal"].str.strip().eq(TIPOLOGIA_TOTAL)
        & periodo.notna()
    )
    resultado = df.loc[mascara, ["Geografía", "Total"]].copy()
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Geografía"]
    )
    resultado["anio"] = pd.to_numeric(periodo.loc[mascara], errors="coerce")
    resultado["total_infracciones"] = convertir_numero_es(
        resultado["Total"], "Total", entero=True
    )

    resultado = resultado[
        ["codigo_ine", "municipio", "anio", "total_infracciones"]
    ]
    validar_claves(
        resultado,
        ["codigo_ine", "anio"],
        nombre="total municipal de infracciones penales",
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
    print(
        "Totales ausentes: "
        f"{df_limpio['total_infracciones'].isna().sum():,}"
    )
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
