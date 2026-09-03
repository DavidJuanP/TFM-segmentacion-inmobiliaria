'''Limpia el paro mensual municipal del SEPE y conserva la censura.

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
MEDIDAS = {
    "total Paro Registrado": "paro_total",
    "Paro hombre edad < 25": "paro_hombre_menor_25",
    "Paro hombre edad 25 -45": "paro_hombre_25_44",
    "Paro hombre edad >=45": "paro_hombre_45_mas",
    "Paro mujer edad < 25": "paro_mujer_menor_25",
    "Paro mujer edad 25 -45": "paro_mujer_25_44",
    "Paro mujer edad >=45": "paro_mujer_45_mas",
    "Paro Agricultura": "paro_agricultura",
    "Paro Industria": "paro_industria",
    "Paro Construcción": "paro_construccion",
    "Paro Servicios": "paro_servicios",
    "Paro Sin empleo Anterior": "paro_sin_empleo_anterior",
}
COLUMNAS_RAW = {*IDENTIFICADORES, *MEDIDAS}


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
        columns={**IDENTIFICADORES, **MEDIDAS}
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

    columnas_medidas = list(MEDIDAS.values())
    for columna in columnas_medidas:
        texto = resultado[columna].str.strip()
        resultado[f"{columna}_censurado"] = texto.eq("<5")
        resultado[columna] = convertir_numero_es(
            texto, columna, entero=True, nulos_adicionales={"<5"}
        )

    validar_claves(resultado, ["codigo_ine", "periodo"], nombre="paro municipal")
    if resultado["mes"].notna().any() and not resultado["mes"].dropna().between(
        1, 12
    ).all():
        raise ValueError("Hay meses fuera del intervalo 1-12")
    resultado = resultado.astype({"anio": "int16", "mes": "int8"})

    columnas = [
        "codigo_ine",
        "municipio",
        "codigo_provincia",
        "provincia",
        "codigo_comunidad",
        "comunidad",
        "periodo",
        "anio",
        "mes",
        "periodo_descripcion",
        *columnas_medidas,
        *(f"{columna}_censurado" for columna in columnas_medidas),
    ]
    return resultado[columnas].sort_values(["codigo_ine", "periodo"]).reset_index(
        drop=True
    )


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
    censuradas = df_limpio.filter(like="_censurado").sum().sum()
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Periodos: {df_limpio['periodo'].nunique():,}")
    print(f"Valores censurados (<5): {censuradas:,}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
