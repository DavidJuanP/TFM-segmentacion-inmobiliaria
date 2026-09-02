'''
Calcula la distancia de cada municipio a la costa.

'''

from pathlib import Path

import pandas as pd
from mpl_toolkits.basemap import Basemap
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform, unary_union

from src.utils.procesamiento_funciones import (
    convertir_numero_es,
    guardar_parquet,
    validar_claves,
    validar_columnas,
)


RUTA_ENTRADA = Path("data/raw/mit/MUNICIPIOS.csv")
RUTA_SALIDA = Path("data/processed/mit/distancia_costa.parquet")
COLUMNAS_RAW = {
    "COD_INE",
    "NOMBRE_ACTUAL",
    "PROVINCIA",
    "LONGITUD_ETRS89_REGCAN95",
    "LATITUD_ETRS89_REGCAN95",
}
PROVINCIAS_CANARIAS = {"35", "38"}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="latin1", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def crear_geometrias_costa():
    mapa = Basemap(
        projection="merc",
        llcrnrlon=-30,
        llcrnrlat=15,
        urcrnrlon=20,
        urcrnrlat=50,
        resolution="i",
    )
    lineas = []
    for poligono, tipo in zip(
        mapa.coastpolygons, mapa.coastpolygontypes
    ):
        if tipo != 1:
            continue
        coordenadas_x, coordenadas_y = poligono
        longitudes, latitudes = mapa(
            coordenadas_x, coordenadas_y, inverse=True
        )
        coordenadas = list(zip(longitudes, latitudes))
        if len(coordenadas) >= 2:
            lineas.append(LineString(coordenadas))

    if not lineas:
        raise ValueError("No se ha podido construir la línea de costa")

    costa_wgs84 = unary_union(lineas)
    a_etrs89_laea = Transformer.from_crs(
        "EPSG:4326", "EPSG:3035", always_xy=True
    )
    a_regcan95_laea = Transformer.from_crs(
        "EPSG:4326", "EPSG:4083", always_xy=True
    )
    costa_etrs89_laea = transform(a_etrs89_laea.transform, costa_wgs84)
    costa_regcan95_laea = transform(a_regcan95_laea.transform, costa_wgs84)
    return (
        costa_etrs89_laea,
        costa_regcan95_laea,
        a_etrs89_laea,
        a_regcan95_laea,
    )


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    resultado = df[list(COLUMNAS_RAW)].copy().rename(
        columns={
            "COD_INE": "codigo_ine",
            "NOMBRE_ACTUAL": "municipio",
            "PROVINCIA": "provincia",
            "LONGITUD_ETRS89_REGCAN95": "longitud",
            "LATITUD_ETRS89_REGCAN95": "latitud",
        }
    )
    resultado["codigo_ine"] = (
        resultado["codigo_ine"].str.strip().str.zfill(11).str[:5]
    )
    for columna in ["municipio", "provincia"]:
        resultado[columna] = resultado[columna].str.strip().mask(
            resultado[columna].str.strip().eq("")
        )
    resultado["longitud"] = convertir_numero_es(
        resultado["longitud"], "LONGITUD_ETRS89_REGCAN95"
    )
    resultado["latitud"] = convertir_numero_es(
        resultado["latitud"], "LATITUD_ETRS89_REGCAN95"
    )
    validar_claves(resultado, ["codigo_ine"], nombre="distancia a la costa")

    (
        costa_etrs89_laea,
        costa_regcan95_laea,
        a_etrs89_laea,
        a_regcan95_laea,
    ) = crear_geometrias_costa()

    def calcular_distancia(fila: pd.Series):
        longitud = fila["longitud"]
        latitud = fila["latitud"]
        if pd.isna(longitud) or pd.isna(latitud):
            return pd.NA

        if fila["codigo_ine"][:2] in PROVINCIAS_CANARIAS:
            x, y = a_regcan95_laea.transform(longitud, latitud)
            costa = costa_regcan95_laea
        else:
            x, y = a_etrs89_laea.transform(longitud, latitud)
            costa = costa_etrs89_laea
        return Point(x, y).distance(costa) / 1_000

    resultado["distancia_costa_km"] = (
        resultado.apply(calcular_distancia, axis="columns")
        .round(2)
        .astype("Float64")
    )
    columnas = [
        "codigo_ine",
        "municipio",
        "provincia",
        "latitud",
        "longitud",
        "distancia_costa_km",
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
    print(
        "Coordenadas ausentes: "
        f"{df_limpio[['latitud', 'longitud']].isna().any(axis=1).sum():,}"
    )
    print(
        "Distancias ausentes: "
        f"{df_limpio['distancia_costa_km'].isna().sum():,}"
    )
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
