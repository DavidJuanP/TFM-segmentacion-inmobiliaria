'''
Calcula la edad media municipal de 2025 y sus variaciones a uno y tres años.

'''

from __future__ import annotations

from collections.abc import Iterable
import os
from pathlib import Path

import pandas as pd

try:
    from src.utils.procesamiento_funciones import (
        convertir_numero_es,
        descargar_archivo_s3,
        guardar_parquet,
        separar_municipio_ine,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )
except ModuleNotFoundError:
    from procesamiento_funciones import (
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
S3_KEY_SALIDA = "ine_edad/edad.parquet"
RUTA_ENTRADA = Path("/tmp/raw/ine/edad.csv")
RUTA_SALIDA = Path("/tmp/processed/ine/edad.parquet")
TAMANO_BLOQUE = 250_000
NUMERO_EDADES = 101
SEXOS = {"Hombres", "Mujeres"}
ANIO_REFERENCIA = 2025
HORIZONTES = {
    1: 2024,
    3: 2022,
}

COLUMNAS_RAW = {
    "Municipios",
    "Sexo",
    "Edad",
    "Periodo",
    "Total",
}
COLUMNAS_AGREGACION = ["codigo_ine", "municipio", "anio"]


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda columna: str(columna).strip(), copy=False)
    if "Edad" not in df.columns:
        candidatas = [
            columna
            for columna in df.columns
            if columna.startswith("Edad (")
        ]
        if len(candidatas) == 1:
            df = df.rename(columns={candidatas[0]: "Edad"}, copy=False)
    return df


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
    df = normalizar_columnas(df)
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
    resultado["anio"] = pd.to_numeric(
        resultado["Periodo"].str.extract(r"(\d{4})", expand=False),
        errors="coerce",
    )
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

    anios_necesarios = {ANIO_REFERENCIA, *HORIZONTES.values()}
    anios_ausentes = anios_necesarios.difference(resultado["anio"].unique())
    if anios_ausentes:
        raise ValueError(
            "Faltan años necesarios para calcular las variaciones de edad: "
            f"{sorted(anios_ausentes)}"
        )

    edad_referencia = resultado.loc[
        resultado["anio"].eq(ANIO_REFERENCIA),
        ["codigo_ine", "municipio", "edad_media"],
    ].rename(columns={"edad_media": "edad_media_2025"})
    validar_claves(
        edad_referencia,
        ["codigo_ine"],
        nombre=f"edad media municipal de {ANIO_REFERENCIA}",
    )

    for numero_anios, anio_anterior in HORIZONTES.items():
        columna_anterior = f"edad_media_{anio_anterior}"
        sufijo = "anio" if numero_anios == 1 else "anios"
        columna_variacion = (
            f"variacion_edad_media_{numero_anios}_{sufijo}"
        )
        edad_anterior = resultado.loc[
            resultado["anio"].eq(anio_anterior),
            ["codigo_ine", "edad_media"],
        ].rename(columns={"edad_media": columna_anterior})
        edad_referencia = edad_referencia.merge(
            edad_anterior,
            on="codigo_ine",
            how="left",
            validate="one_to_one",
        )
        edad_referencia[columna_variacion] = (
            edad_referencia["edad_media_2025"]
            - edad_referencia.pop(columna_anterior)
        ).round(2).astype("Float64")

    validar_claves(
        edad_referencia,
        ["codigo_ine"],
        nombre="variaciones de edad media",
    )
    columnas = [
        "codigo_ine",
        "municipio",
        "edad_media_2025",
        "variacion_edad_media_1_anio",
        "variacion_edad_media_3_anios",
    ]
    return edad_referencia[columnas].sort_values(
        "codigo_ine"
    ).reset_index(drop=True)


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
    print(f"Año de referencia: {ANIO_REFERENCIA}")
    print(
        "Edades medias de 2025 ausentes: "
        f"{df_limpio['edad_media_2025'].isna().sum():,}"
    )
    for numero_anios in HORIZONTES:
        sufijo = "anio" if numero_anios == 1 else "anios"
        columna = f"variacion_edad_media_{numero_anios}_{sufijo}"
        print(
            f"Variaciones a {numero_anios} año(s) ausentes: "
            f"{df_limpio[columna].isna().sum():,}"
        )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
