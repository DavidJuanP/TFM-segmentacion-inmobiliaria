"""Limpia los saldos migratorios municipales del INE."""

from pathlib import Path

import pandas as pd

from src.processing._common import (
    convertir_numero_es,
    guardar_parquet,
    separar_municipio_ine,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/ine/migracion.csv")
RUTA_SALIDA = Path("data/processed/ine/migracion.parquet")
COLUMNAS_RAW = {"Municipios", "Sexo", "Tipo de saldo", "Periodo", "Total"}
TIPOS_SALDO = {
    "Saldo total": "saldo_total",
    "Saldo interior": "saldo_interior",
    "Saldo exterior": "saldo_exterior",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    mascara = df["Municipios"].notna() & df["Sexo"].str.strip().str.casefold().eq(
        "ambos sexos"
    )
    resultado = df.loc[
        mascara, ["Municipios", "Tipo de saldo", "Periodo", "Total"]
    ].copy()
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["tipo_saldo"] = resultado["Tipo de saldo"].map(TIPOS_SALDO)
    resultado["saldo"] = convertir_numero_es(resultado["Total"], "Total", entero=True)
    validar_claves(
        resultado,
        ["codigo_ine", "anio", "tipo_saldo"],
        nombre="saldos migratorios",
    )

    resultado = resultado.pivot(
        index=["codigo_ine", "municipio", "anio"],
        columns="tipo_saldo",
        values="saldo",
    ).reset_index()
    resultado.columns.name = None
    for columna in TIPOS_SALDO.values():
        if columna not in resultado:
            resultado[columna] = pd.NA
        resultado[columna] = resultado[columna].astype("Int64")
    resultado["anio"] = resultado["anio"].astype("int16")

    columnas = ["codigo_ine", "municipio", "anio", *TIPOS_SALDO.values()]
    return resultado[columnas].sort_values(["codigo_ine", "anio"]).reset_index(
        drop=True
    )


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
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
