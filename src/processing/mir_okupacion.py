'''
Normaliza los hechos de okupación por comunidad autónoma y año del MIR.

'''

from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/mir/okupacion.csv")
RUTA_SALIDA = Path("data/processed/mir/okupacion.parquet")
COLUMNAS_RAW = {"Comunidades autónomas", "periodo", "Total"}
GEOGRAFIAS_EXCLUIDAS = {
    "TOTAL NACIONAL",
    "DESCONOCIDA",
    "EN EL EXTRANJERO",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    resultado = df[["Comunidades autónomas", "periodo", "Total"]].copy()
    resultado["comunidad"] = resultado["Comunidades autónomas"].str.strip()
    resultado = resultado.loc[
        resultado["comunidad"].notna()
        & resultado["comunidad"].ne("")
        & ~resultado["comunidad"].isin(GEOGRAFIAS_EXCLUIDAS)
    ].copy()
    resultado["anio"] = pd.to_numeric(resultado["periodo"], errors="coerce")
    resultado["total_okupaciones"] = convertir_numero_es(
        resultado["Total"], "Total", entero=True
    )

    resultado = resultado[["comunidad", "anio", "total_okupaciones"]]
    validar_claves(
        resultado,
        ["comunidad", "anio"],
        nombre="okupación por comunidad autónoma",
    )
    resultado["anio"] = resultado["anio"].astype("int16")
    return resultado.sort_values(["comunidad", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Comunidades: {df_limpio['comunidad'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(
        "Totales ausentes: "
        f"{df_limpio['total_okupaciones'].isna().sum():,}"
    )
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
