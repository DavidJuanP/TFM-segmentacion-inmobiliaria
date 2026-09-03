'''
Calcula la edad media municipal a partir de la población por edad del INE.

'''

from collections.abc import Iterable
import os
from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    descargar_archivo_s3,
    guardar_parquet,
    separar_municipio_ine,
    subir_archivo_s3,
    validar_claves,
    validar_columnas,
)


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "ine/edad.csv"
S3_KEY_SALIDA = "ine/edad.parquet"
RUTA_ENTRADA = Path("/tmp/raw/ine/edad.csv")
RUTA_SALIDA = Path("/tmp/processed/ine/edad.parquet")
TAMANO_BLOQUE = 250_000
NUMERO_EDADES = 101
SEXOS = {"Hombres", "Mujeres"}

COLUMNAS_RAW = {
    "Municipios",
    "Sexo",
    "Edad",
    "Periodo",
    "Total",
}
COLUMNAS_AGREGACION = ["codigo_ine", "municipio", "anio"]


def leer_datos(
    ruta: Path = RUTA_ENTRADA,
) -> Iterable[pd.DataFrame]:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    return pd.read_csv(
        ruta,
        sep=";",
        encoding="utf-8",
        dtype="string",
        chunksize=TAMANO_BLOQUE,
    )


def agregar_bloque(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    edad = pd.to_numeric(
        df["Edad"].str.extract(r"^(\d+)", expand=False),
        errors="coerce",
    )
    mascara = (
        df["Municipios"].notna()
        & df["Sexo"].str.strip().isin(SEXOS)
        & edad.notna()
    )
    resultado = df.loc[
        mascara, ["Municipios", "Sexo", "Periodo", "Total"]
    ].copy()
    resultado["edad"] = edad.loc[mascara]
    resultado["codigo_ine"], resultado["municipio"] = separar_municipio_ine(
        resultado["Municipios"]
    )
    resultado["sexo"] = resultado["Sexo"].str.strip()
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    resultado["poblacion_edad"] = convertir_numero_es(
        resultado["Total"],
        "Total",
        entero=True,
        nulos_adicionales={"."},
    )

    if not resultado["edad"].dropna().between(0, 100).all():
        raise ValueError("Hay edades fuera del intervalo esperado 0-100")
    validar_claves(
        resultado,
        ["codigo_ine", "anio", "sexo", "edad"],
        nombre="población municipal por edad",
    )

    resultado["suma_edades"] = resultado["edad"] * resultado["poblacion_edad"]
    resultado["valor_ausente"] = resultado["poblacion_edad"].isna().astype("int64")
    return resultado.groupby(COLUMNAS_AGREGACION, as_index=False).agg(
        suma_edades=("suma_edades", "sum"),
        poblacion_con_edad=("poblacion_edad", "sum"),
        observaciones=("edad", "size"),
        valores_ausentes=("valor_ausente", "sum"),
    )


def procesar_datos(
    datos: pd.DataFrame | Iterable[pd.DataFrame],
) -> pd.DataFrame:
    bloques = [datos] if isinstance(datos, pd.DataFrame) else datos
    parciales = []
    for bloque in bloques:
        parcial = agregar_bloque(bloque)
        if not parcial.empty:
            parciales.append(parcial)

    if not parciales:
        raise ValueError("No se encontraron datos municipales por edad")

    resultado = pd.concat(parciales, ignore_index=True)
    resultado = resultado.groupby(COLUMNAS_AGREGACION, as_index=False).agg(
        suma_edades=("suma_edades", "sum"),
        poblacion_con_edad=("poblacion_con_edad", "sum"),
        observaciones=("observaciones", "sum"),
        valores_ausentes=("valores_ausentes", "sum"),
    )
    datos_incompletos = (
        resultado["valores_ausentes"].gt(0)
        | resultado["observaciones"].ne(NUMERO_EDADES * len(SEXOS))
        | resultado["poblacion_con_edad"].le(0)
    )
    resultado["edad_media"] = (
        resultado["suma_edades"] / resultado["poblacion_con_edad"]
    ).mask(datos_incompletos).round(2).astype("Float64")

    resultado = resultado[[*COLUMNAS_AGREGACION, "edad_media"]]
    validar_claves(
        resultado,
        ["codigo_ine", "anio"],
        nombre="edad media municipal",
    )
    resultado["anio"] = resultado["anio"].astype("int16")
    return resultado.sort_values(["codigo_ine", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ENTRADA, RUTA_ENTRADA)
    df_limpio = procesar_datos(leer_datos())
    guardar_datos(df_limpio)
    salida_s3 = subir_archivo_s3(
        RUTA_SALIDA, PROCESSED_BUCKET, S3_KEY_SALIDA
    )
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Edades medias ausentes: {df_limpio['edad_media'].isna().sum():,}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
