'''
Calcula el tamaño medio del hogar por municipio a partir de datos del INE.

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


RUTA_ENTRADA = Path("data/raw/ine/tamanio_hogar.csv")
RUTA_SALIDA = Path("data/processed/ine/tamanio_hogar.parquet")
COLUMNAS_RAW = {"Municipio", "Tamaño del hogar", "Total"}
TAMANIOS = {
    "1 persona": 1,
    "2 personas": 2,
    "3 personas": 3,
    "4 personas": 4,
    # El INE agrupa todos los hogares de cinco miembros o más. Se utiliza el
    # límite inferior, por lo que la media resultante es una aproximación.
    "5 o más personas": 5,
}
CATEGORIA_TOTAL = "Total (tamaño del hogar)"


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_RAW)
    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_RAW)
    filas_municipales = df["Municipio"].str.match(r"^\d{5}\s+", na=False)

    detalle = df.loc[
        filas_municipales & df["Tamaño del hogar"].isin(TAMANIOS),
        ["Municipio", "Tamaño del hogar", "Total"],
    ].copy()
    detalle["codigo_ine"], detalle["municipio"] = separar_municipio_ine(
        detalle["Municipio"]
    )
    detalle["miembros"] = detalle["Tamaño del hogar"].map(TAMANIOS).astype("int8")
    detalle["hogares"] = convertir_numero_es(
        detalle["Total"], "Total", entero=True
    )
    validar_claves(
        detalle,
        ["codigo_ine", "Tamaño del hogar"],
        nombre="hogares por tamaño",
    )

    detalle["miembros_ponderados"] = detalle["miembros"] * detalle["hogares"]
    detalle["valor_ausente"] = detalle["hogares"].isna().astype("int8")
    resultado = detalle.groupby(
        ["codigo_ine", "municipio"], as_index=False
    ).agg(
        miembros_ponderados=("miembros_ponderados", "sum"),
        hogares=("hogares", "sum"),
        categorias=("miembros", "size"),
        valores_ausentes=("valor_ausente", "sum"),
    )

    totales = df.loc[
        filas_municipales & df["Tamaño del hogar"].eq(CATEGORIA_TOTAL),
        ["Municipio", "Total"],
    ].copy()
    totales["codigo_ine"], _ = separar_municipio_ine(totales["Municipio"])
    totales["hogares_publicados"] = convertir_numero_es(
        totales["Total"], "Total", entero=True
    )
    validar_claves(totales, ["codigo_ine"], nombre="total de hogares")
    resultado = resultado.merge(
        totales[["codigo_ine", "hogares_publicados"]],
        on="codigo_ine",
        how="left",
        validate="one_to_one",
    )

    totales_incoherentes = (
        resultado["hogares_publicados"].notna()
        & resultado["hogares"].ne(resultado["hogares_publicados"])
    )
    if totales_incoherentes.any():
        ejemplos = resultado.loc[
            totales_incoherentes,
            ["codigo_ine", "hogares", "hogares_publicados"],
        ].head(5).to_dict("records")
        raise ValueError(
            "La suma de hogares por tamaño no coincide con el total publicado. "
            f"Ejemplos: {ejemplos}"
        )

    datos_incompletos = (
        resultado["categorias"].ne(len(TAMANIOS))
        | resultado["valores_ausentes"].gt(0)
        | resultado["hogares"].le(0)
    )
    resultado["tamanio_medio_hogar"] = (
        resultado["miembros_ponderados"] / resultado["hogares"]
    ).mask(datos_incompletos).round(2).astype("Float64")

    resultado = resultado[["codigo_ine", "municipio", "tamanio_medio_hogar"]]
    validar_claves(resultado, ["codigo_ine"], nombre="tamaño medio del hogar")
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
        "Tamaños medios ausentes: "
        f"{df_limpio['tamanio_medio_hogar'].isna().sum():,}"
    )
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
