'''
Extrae las viviendas totales, vacías y de uso esporádico por municipio del INE.

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


RUTA_ENTRADA = Path("data/raw/ine/viviendas.csv")
RUTA_SALIDA = Path("data/processed/ine/viviendas.parquet")
COLUMNAS_RAW = {"Municipios", "Consumo eléctrico", "Total"}
METRICAS = {
    "Viviendas totales": "viviendas_totales",
    "Viviendas vacías": "viviendas_vacias",
    "Viviendas de uso esporádico": "viviendas_uso_esporadico",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    mascara = df["Municipios"].notna() & df["Consumo eléctrico"].isin(METRICAS)
    resultado = df.loc[
        mascara, ["Municipios", "Consumo eléctrico", "Total"]
    ].copy()
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["metrica"] = resultado["Consumo eléctrico"].map(METRICAS)
    resultado["valor"] = convertir_numero_es(
        resultado["Total"], "Total", entero=True
    )
    validar_claves(
        resultado,
        ["codigo_ine", "metrica"],
        nombre="viviendas municipales según uso",
    )

    resultado = resultado.pivot(
        index=["codigo_ine", "municipio"],
        columns="metrica",
        values="valor",
    ).reset_index()
    resultado.columns.name = None
    for columna in METRICAS.values():
        if columna not in resultado:
            resultado[columna] = pd.NA
        resultado[columna] = resultado[columna].astype("Int64")

    columnas_parciales = ["viviendas_vacias", "viviendas_uso_esporadico"]
    valores_incoherentes = resultado[columnas_parciales].gt(
        resultado["viviendas_totales"], axis="index"
    ).any(axis="columns")
    if valores_incoherentes.any():
        ejemplos = resultado.loc[
            valores_incoherentes,
            ["codigo_ine", "viviendas_totales", *columnas_parciales],
        ].head(5).to_dict("records")
        raise ValueError(
            "Hay municipios con una categoría de uso mayor que el total de "
            "viviendas. "
            f"Ejemplos: {ejemplos}"
        )

    suma_incoherente = resultado[columnas_parciales].sum(
        axis="columns", min_count=len(columnas_parciales)
    ).gt(resultado["viviendas_totales"])
    if suma_incoherente.any():
        ejemplos = resultado.loc[
            suma_incoherente,
            ["codigo_ine", "viviendas_totales", *columnas_parciales],
        ].head(5).to_dict("records")
        raise ValueError(
            "Hay municipios donde las viviendas vacías y de uso esporádico "
            "superan conjuntamente las viviendas totales. "
            f"Ejemplos: {ejemplos}"
        )

    columnas = [
        "codigo_ine",
        "municipio",
        "viviendas_totales",
        "viviendas_vacias",
        "viviendas_uso_esporadico",
    ]
    resultado = resultado[columnas]
    validar_claves(resultado, ["codigo_ine"], nombre="viviendas municipales")
    return resultado.sort_values("codigo_ine").reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Municipios guardados: {len(df_limpio):,}")
    print(
        "Totales de viviendas ausentes: "
        f"{df_limpio['viviendas_totales'].isna().sum():,}"
    )
    print(
        "Totales de viviendas vacías ausentes: "
        f"{df_limpio['viviendas_vacias'].isna().sum():,}"
    )
    print(
        "Totales de viviendas de uso esporádico ausentes: "
        f"{df_limpio['viviendas_uso_esporadico'].isna().sum():,}"
    )
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
