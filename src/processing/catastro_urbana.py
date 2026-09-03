'''
Normaliza las estadísticas municipales del Catastro Inmobiliario Urbano.

'''

import os
from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    descargar_archivo_s3,
    guardar_parquet,
    subir_archivo_s3,
    validar_claves,
    validar_columnas,
)


RAW_BUCKET = os.environ["RAW_BUCKET"]
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_ENTRADA = "catastro/URBANA2026.xls"
S3_KEY_SALIDA = "catastro/urbana.parquet"
RUTA_ENTRADA = Path("/tmp/raw/catastro/URBANA2026.xls")
RUTA_SALIDA = Path("/tmp/processed/catastro/urbana.parquet")

COLUMNAS = {
    "AREF": "anio",
    "NOM_CCAA": "comunidad",
    "COD_INE_CCAA": "codigo_comunidad",
    "NOM_PROV": "provincia",
    "COD_INE_PROV": "codigo_provincia",
    "NOM_MUNI": "municipio",
    "COD_INE_MUNI": "codigo_ine",
    "ULT_REVISION": "anio_ultima_revision",
    "UURBANAS": "inmuebles_urbanos",
    "V_CATASTRAL": "valor_catastral_total_eur",
    "V_CONSTRUCCION": "valor_catastral_construccion_eur",
    "V_SUELO": "valor_catastral_suelo_eur",
    "SUPERF_URB": "superficie_urbana_m2",
    "PARCELAS_URB": "parcelas_urbanas",
    "UU_ALMACEN": "inmuebles_almacen_estacionamiento",
    "V_CAT_ALMACEN": "valor_catastral_almacen_estacionamiento_eur",
    "UU_COMERCIAL": "inmuebles_comerciales",
    "V_CAT_COMERCIAL": "valor_catastral_comercial_eur",
    "UU_CULTURAL": "inmuebles_culturales",
    "V_CAT_CULTURAL": "valor_catastral_cultural_eur",
    "UU_HOSTELERIA": "inmuebles_hosteleria",
    "V_CAT_HOSTELERIA": "valor_catastral_hosteleria_eur",
    "UU_INDUSTRIAL": "inmuebles_industriales",
    "V_CAT_INDUSTRIAL": "valor_catastral_industrial_eur",
    "UU_DEPORTIVO": "inmuebles_deportivos",
    "V_CAT_DEPORTIVO": "valor_catastral_deportivo_eur",
    "UU_SOLAR": "solares",
    "V_CAT_SOLAR": "valor_catastral_solares_eur",
    "UU_OFICINAS": "inmuebles_oficinas",
    "V_CAT_OFICINAS": "valor_catastral_oficinas_eur",
    "UU_SINGULAR": "inmuebles_singulares",
    "V_CAT_SINGULAR": "valor_catastral_singular_eur",
    "UU_RELIGIOSO": "inmuebles_religiosos",
    "V_CAT_RELIGIOSO": "valor_catastral_religioso_eur",
    "UU_ESPECTACULOS": "inmuebles_espectaculos",
    "V_CAT_ESPECTACULOS": "valor_catastral_espectaculos_eur",
    "UU_RES": "inmuebles_residenciales",
    "V_CAT_RES": "valor_catastral_residencial_eur",
    "UU_SANIDAD": "inmuebles_sanitarios",
    "V_CAT_SANIDAD": "valor_catastral_sanitario_eur",
}

COLUMNAS_ENTERAS = {
    "AREF",
    "ULT_REVISION",
    "UURBANAS",
    "SUPERF_URB",
    "PARCELAS_URB",
    "UU_ALMACEN",
    "UU_COMERCIAL",
    "UU_CULTURAL",
    "UU_HOSTELERIA",
    "UU_INDUSTRIAL",
    "UU_DEPORTIVO",
    "UU_SOLAR",
    "UU_OFICINAS",
    "UU_SINGULAR",
    "UU_RELIGIOSO",
    "UU_ESPECTACULOS",
    "UU_RES",
    "UU_SANIDAD",
}

COLUMNAS_VALOR = {
    "V_CATASTRAL",
    "V_CONSTRUCCION",
    "V_SUELO",
    "V_CAT_ALMACEN",
    "V_CAT_COMERCIAL",
    "V_CAT_CULTURAL",
    "V_CAT_HOSTELERIA",
    "V_CAT_INDUSTRIAL",
    "V_CAT_DEPORTIVO",
    "V_CAT_SOLAR",
    "V_CAT_OFICINAS",
    "V_CAT_SINGULAR",
    "V_CAT_RELIGIOSO",
    "V_CAT_ESPECTACULOS",
    "V_CAT_RES",
    "V_CAT_SANIDAD",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_excel(ruta, engine="xlrd", dtype="string")
    validar_columnas(df, COLUMNAS)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS)
    resultado = df[list(COLUMNAS)].copy()

    for columna in COLUMNAS_ENTERAS:
        resultado[columna] = convertir_numero_es(
            resultado[columna], columna, entero=True, decimal_coma=False
        )
    for columna in COLUMNAS_VALOR:
        resultado[columna] = convertir_numero_es(
            resultado[columna], columna, decimal_coma=False
        ).round(2)

    for columna, longitud in {
        "COD_INE_CCAA": 2,
        "COD_INE_PROV": 2,
        "COD_INE_MUNI": 5,
    }.items():
        resultado[columna] = resultado[columna].str.strip().str.zfill(longitud)
    for columna in ["NOM_CCAA", "NOM_PROV", "NOM_MUNI"]:
        resultado[columna] = resultado[columna].str.strip().mask(
            resultado[columna].str.strip().eq("")
        )

    resultado = resultado.rename(columns=COLUMNAS)
    validar_claves(
        resultado,
        ["codigo_ine", "anio"],
        nombre="estadísticas municipales del Catastro urbano",
    )
    resultado["anio"] = resultado["anio"].astype("int16")
    resultado["anio_ultima_revision"] = resultado[
        "anio_ultima_revision"
    ].astype("int16")
    return resultado[list(COLUMNAS.values())].sort_values(
        ["codigo_ine", "anio"]
    ).reset_index(drop=True)


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
    print(
        "Inmuebles residenciales ausentes: "
        f"{df_limpio['inmuebles_residenciales'].isna().sum():,}"
    )
    print(
        "Valores catastrales residenciales ausentes: "
        f"{df_limpio['valor_catastral_residencial_eur'].isna().sum():,}"
    )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
