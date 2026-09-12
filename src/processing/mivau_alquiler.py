'''
Normaliza los indicadores municipales de alquiler del MIVAU y sustituye los
percentiles 25 y 75 por su rango intercuartílico. El recuento de viviendas
testigo se descarta de la salida.

'''

import os
from pathlib import Path

import pandas as pd

try:
    from src.utils.procesamiento_funciones import (
        convertir_numero_es,
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )
except ModuleNotFoundError:
    from procesamiento_funciones import (
        convertir_numero_es,
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "mivau/alquiler.csv"
S3_KEY_SALIDA = "mivau_alquiler/alquiler.parquet"
RUTA_ENTRADA = Path("/tmp/raw/mivau/alquiler.csv")
RUTA_SALIDA = Path("/tmp/processed/mivau/alquiler.parquet")
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
    medidas_disponibles = set(resultado["tipo_medida"].dropna())
    percentiles_necesarios = {"PERCENT25", "PERCENT75"}
    percentiles_ausentes = percentiles_necesarios.difference(
        medidas_disponibles
    )
    if percentiles_ausentes:
        raise ValueError(
            "Faltan percentiles para calcular el rango intercuartílico: "
            f"{sorted(percentiles_ausentes)}"
        )

    # El rango intercuartílico conserva la dispersión central en una sola
    # variable: IQR = percentil 75 - percentil 25.
    dimensiones = [
        "codigo_ine",
        "municipio",
        "codigo_provincia",
        "provincia",
        "anio",
        "tipo_vivienda",
        "elemento",
    ]
    percentil_25 = resultado.loc[
        resultado["tipo_medida"].eq("PERCENT25"),
        [*dimensiones, "valor"],
    ].rename(columns={"valor": "percentil_25"})
    percentil_75 = resultado.loc[
        resultado["tipo_medida"].eq("PERCENT75"),
        [*dimensiones, "valor"],
    ].rename(columns={"valor": "percentil_75"})
    rangos = percentil_25.merge(
        percentil_75,
        on=dimensiones,
        how="outer",
        validate="one_to_one",
    )
    rangos["tipo_medida"] = "RANGO_INTERCUARTILICO"
    rangos["valor"] = (
        rangos["percentil_75"] - rangos["percentil_25"]
    ).round(2).astype("Float64")
    rangos_negativos = rangos["valor"].lt(0).fillna(False)
    if rangos_negativos.any():
        ejemplos = rangos.loc[
            rangos_negativos,
            ["codigo_ine", "anio", "elemento", "tipo_vivienda", "valor"],
        ].head(5).to_dict("records")
        raise ValueError(
            "Hay rangos intercuartílicos negativos. "
            f"Ejemplos: {ejemplos}"
        )
    rangos = rangos[[*dimensiones, "tipo_medida", "valor"]]

    resultado = pd.concat(
        [
            resultado.loc[
                resultado["tipo_medida"].eq("MEDIANA")
            ],
            rangos,
        ],
        ignore_index=True,
    )
    validar_claves(
        resultado,
        claves,
        nombre="indicadores de alquiler con rango intercuartílico",
    )
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
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Valores ausentes: {df_limpio['valor'].isna().sum():,}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
