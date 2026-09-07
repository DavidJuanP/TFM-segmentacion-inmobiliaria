'''Calcula el paro medio municipal de 2025 a partir de los datos del SEPE.

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
S3_KEY_ENTRADA = "sepe/paro.csv"
S3_KEY_SALIDA = "sepe/paro.parquet"
RUTA_ENTRADA = Path("/tmp/raw/sepe/paro.csv")
RUTA_SALIDA = Path("/tmp/processed/sepe/paro.parquet")

IDENTIFICADORES = {
    "Código mes": "codigo_mes",
    "mes": "periodo_descripcion",
    "Código de CA": "codigo_comunidad",
    "Comunidad Autónoma": "comunidad",
    "Codigo Provincia": "codigo_provincia",
    "Provincia": "provincia",
    "Codigo Municipio": "codigo_ine",
    "Municipio": "municipio",
}
COLUMNA_PARO_TOTAL = "total Paro Registrado"
ANIO_MEDIA = 2025
MESES_ANIO = 12
COLUMNAS_RAW = {*IDENTIFICADORES, COLUMNA_PARO_TOTAL}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    # La primera línea es un título; la segunda contiene la cabecera real.
    df = pd.read_csv(
        ruta, sep=";", encoding="cp1252", dtype="string", skiprows=1
    )
    df.columns = df.columns.str.strip()
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df[list(COLUMNAS_RAW)].copy().rename(
        columns={**IDENTIFICADORES, COLUMNA_PARO_TOTAL: "paro_total"}
    )
    resultado["codigo_mes"] = resultado["codigo_mes"].str.strip()
    periodo = resultado["codigo_mes"].str.extract(r"^(\d{4})(\d{2})$")
    resultado["anio"] = pd.to_numeric(periodo[0], errors="coerce")
    resultado["mes"] = pd.to_numeric(periodo[1], errors="coerce")
    resultado["periodo"] = periodo[0] + "-" + periodo[1]
    resultado["codigo_comunidad"] = (
        resultado["codigo_comunidad"].str.strip().str.zfill(2)
    )
    resultado["codigo_provincia"] = (
        resultado["codigo_provincia"].str.strip().str.zfill(2)
    )
    resultado["codigo_ine"] = resultado["codigo_ine"].str.strip().str.zfill(5)
    for columna in [
        "periodo_descripcion",
        "comunidad",
        "provincia",
        "municipio",
    ]:
        resultado[columna] = resultado[columna].str.strip()

    texto_paro = resultado["paro_total"].str.strip()
    resultado["paro_total_censurado"] = texto_paro.eq("<5")
    resultado["paro_total"] = convertir_numero_es(
        texto_paro, "paro_total", entero=True, nulos_adicionales={"<5"}
    )

    validar_claves(resultado, ["codigo_ine", "periodo"], nombre="paro municipal")
    if resultado["mes"].notna().any() and not resultado["mes"].dropna().between(
        1, 12
    ).all():
        raise ValueError("Hay meses fuera del intervalo 1-12")
    resultado = resultado.astype({"anio": "int16", "mes": "int8"})

    datos_2025 = resultado.loc[resultado["anio"].eq(ANIO_MEDIA)]
    if datos_2025.empty:
        raise ValueError(f"No hay datos de paro para el año {ANIO_MEDIA}")

    medias_2025 = datos_2025.groupby("codigo_ine", as_index=False).agg(
        paro_medio_2025=("paro_total", "mean"),
        meses_2025=("mes", "nunique"),
    )
    incompletos = medias_2025[medias_2025["meses_2025"].ne(MESES_ANIO)]
    if not incompletos.empty:
        ejemplos = ", ".join(incompletos["codigo_ine"].head(10))
        raise ValueError(
            f"Hay {len(incompletos)} municipios sin los {MESES_ANIO} meses "
            f"de {ANIO_MEDIA}. Ejemplos: {ejemplos}"
        )
    medias_2025["paro_medio_2025"] = (
        medias_2025["paro_medio_2025"].round(2).astype("Float64")
    )
    columnas_identificadoras = [
        "codigo_ine",
        "municipio",
        "codigo_provincia",
        "provincia",
        "codigo_comunidad",
        "comunidad",
        "anio",
    ]
    identificadores = datos_2025[columnas_identificadoras].drop_duplicates()
    validar_claves(
        identificadores,
        ["codigo_ine"],
        nombre="identificadores municipales del paro",
    )
    resultado = identificadores.merge(
        medias_2025[["codigo_ine", "paro_medio_2025"]],
        on="codigo_ine",
        how="left",
        validate="one_to_one",
    )

    columnas = [
        *columnas_identificadoras,
        "paro_medio_2025",
    ]
    resultado = resultado[columnas]
    validar_claves(
        resultado,
        ["codigo_ine"],
        nombre="paro medio municipal de 2025",
    )
    return resultado.sort_values("codigo_ine").reset_index(drop=True)


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
    medias_ausentes = df_limpio["paro_medio_2025"].isna().sum()
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Año: {ANIO_MEDIA}")
    print(f"Paros medios de 2025 ausentes: {medias_ausentes:,}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
