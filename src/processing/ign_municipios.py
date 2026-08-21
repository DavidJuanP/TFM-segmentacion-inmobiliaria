'''
Limpia el catálogo municipal del IGN y lo guarda en Parquet.

'''

from pathlib import Path

import pandas as pd

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/ign/municipios.xlsx")
RUTA_SALIDA = Path("data/processed/ign/municipios.parquet")
HOJA = "IGN_INFOGEO_MUNICIPIOS"

COLUMNAS_RAW = {
    "Identificador",
    "Nombre",
    "Población",
    "Superficie (km2)",
    "Capital",
    "Provincia",
    "Ver en mapa",
}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_excel(ruta, sheet_name=HOJA, dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df[list(COLUMNAS_RAW)].copy().rename(
        columns={
            "Identificador": "codigo_ine",
            "Nombre": "municipio",
            "Población": "poblacion",
            "Superficie (km2)": "superficie_km2",
            "Capital": "capital",
            "Provincia": "provincia",
            "Ver en mapa": "url_mapa",
        }
    )
    resultado["codigo_ine"] = resultado["codigo_ine"].str.strip().str.zfill(5)
    for columna in ["municipio", "capital", "provincia", "url_mapa"]:
        resultado[columna] = resultado[columna].str.strip().mask(
            resultado[columna].str.strip().eq("")
        )

    resultado["poblacion"] = convertir_numero_es(
        resultado["poblacion"], "Población", entero=True
    )
    resultado["superficie_km2"] = convertir_numero_es(
        resultado["superficie_km2"], "Superficie (km2)", decimal_coma=False
    )
    coordenadas = resultado["url_mapa"].str.extract(
        r"[?&]center=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"
    )
    resultado["longitud"] = pd.to_numeric(coordenadas[0], errors="coerce").astype(
        "Float64"
    )
    resultado["latitud"] = pd.to_numeric(coordenadas[1], errors="coerce").astype(
        "Float64"
    )

    validar_claves(resultado, ["codigo_ine"], nombre="municipios del IGN")
    columnas = [
        "codigo_ine",
        "municipio",
        "provincia",
        "capital",
        "poblacion",
        "superficie_km2",
        "longitud",
        "latitud",
        "url_mapa",
    ]
    return resultado[columnas].sort_values("codigo_ine").reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Municipios guardados: {len(df_limpio):,}")
    print(f"Coordenadas ausentes: {df_limpio['latitud'].isna().sum():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
