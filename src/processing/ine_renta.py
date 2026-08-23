'''
Limpia los indicadores municipales de renta del Atlas del INE.

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


RUTA_ENTRADA = Path("data/raw/ine/renta.csv")
RUTA_SALIDA = Path("data/processed/ine/renta.parquet")
TAMANO_BLOQUE = 250_000

COLUMNAS_RAW = {
    "Municipios",
    "Distritos",
    "Secciones",
    "Indicadores de renta media",
    "Periodo",
    "Total",
}
METRICAS = {
    "Renta neta media por persona": "renta_neta_media_persona_eur",
    "Renta neta media por hogar": "renta_neta_media_hogar_eur",
    "Renta bruta media por persona": "renta_bruta_media_persona_eur",
    "Renta bruta media por hogar": "renta_bruta_media_hogar_eur",
    "Media de la renta por unidad de consumo": "renta_media_unidad_consumo_eur",
    "Mediana de la renta por unidad de consumo": "renta_mediana_unidad_consumo_eur",
}


def seleccionar_filas_municipales(df: pd.DataFrame) -> pd.DataFrame:
    # Los agregados municipales no tienen distrito ni sección informados.
    municipio_informado = df["Municipios"].notna() & df[
        "Municipios"
    ].str.strip().ne("")
    distrito_vacio = df["Distritos"].isna() | df["Distritos"].str.strip().eq("")
    seccion_vacia = df["Secciones"].isna() | df["Secciones"].str.strip().eq("")
    return df.loc[municipio_informado & distrito_vacio & seccion_vacia].copy()


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")

    partes = []
    lector = pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8",
        dtype="string",
        chunksize=TAMANO_BLOQUE,
    )
    for bloque in lector:
        validar_columnas(bloque, COLUMNAS_RAW)
        partes.append(seleccionar_filas_municipales(bloque))

    if not partes:
        raise ValueError(f"El fichero de entrada está vacío: {ruta}")
    return pd.concat(partes, ignore_index=True)


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    resultado = seleccionar_filas_municipales(df)
    resultado = resultado[
        ["Municipios", "Indicadores de renta media", "Periodo", "Total"]
    ].copy()

    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["metrica"] = resultado["Indicadores de renta media"].map(METRICAS)
    resultado["valor"] = convertir_numero_es(
        resultado["Total"],
        "Total",
        entero=True,
        nulos_adicionales={"."},
    )
    validar_claves(
        resultado,
        ["codigo_ine", "anio", "metrica"],
        nombre="indicadores municipales de renta",
    )

    resultado = resultado.pivot(
        index=["codigo_ine", "municipio", "anio"],
        columns="metrica",
        values="valor",
    ).reset_index()
    resultado.columns.name = None
    for columna in METRICAS.values():
        if columna not in resultado:
            resultado[columna] = pd.NA
        resultado[columna] = resultado[columna].astype("Int64")
    resultado["anio"] = resultado["anio"].astype("int16")

    columnas = ["codigo_ine", "municipio", "anio", *METRICAS.values()]
    return resultado[columnas].sort_values(["codigo_ine", "anio"]).reset_index(
        drop=True
    )


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    valores_ausentes = df_limpio[list(METRICAS.values())].isna().sum().sum()
    print(f"Filas municipales leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Valores de renta ausentes: {valores_ausentes:,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
