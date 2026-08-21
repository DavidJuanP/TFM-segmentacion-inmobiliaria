"""Limpia el CSV de población municipal del INE y lo guarda en Parquet."""

from pathlib import Path

import pandas as pd


RUTA_ENTRADA = Path("data/raw/ine/poblacion.csv")
RUTA_SALIDA = Path("data/processed/ine/poblacion.parquet")

COLUMNAS_RAW = {"Municipios", "Sexo", "Periodo", "Total"}


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    """Lee todas las columnas como texto para controlar las conversiones."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")

    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")

    columnas_faltantes = COLUMNAS_RAW.difference(df.columns)
    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas: "
            f"{sorted(columnas_faltantes)}. Disponibles: {df.columns.tolist()}"
        )

    return df


def procesar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Selecciona la población total y normaliza claves y tipos."""
    # El fichero contiene Total, Hombres y Mujeres. Para obtener una sola fila
    # por municipio y año conservamos exclusivamente la población total.
    resultado = df.loc[
        df["Sexo"].str.strip().str.casefold().eq("total"),
        ["Municipios", "Periodo", "Total"],
    ].copy()

    resultado["codigo_ine"] = resultado["Municipios"].str.extract(
        r"^(\d{5})", expand=False
    )
    resultado["municipio"] = (
        resultado["Municipios"]
        .str.replace(r"^\d{5}\s+", "", regex=True)
        .str.strip()
    )
    resultado["anio"] = pd.to_numeric(resultado["Periodo"], errors="coerce")
    total_normalizado = resultado["Total"].str.replace(".", "", regex=False)
    resultado["poblacion"] = pd.to_numeric(total_normalizado, errors="coerce")

    columnas_finales = ["codigo_ine", "municipio", "anio", "poblacion"]
    resultado = resultado[columnas_finales]

    claves_invalidas = (
        resultado[["codigo_ine", "municipio", "anio"]].isna().any(axis=1)
    )
    if claves_invalidas.any():
        ejemplos = resultado.loc[claves_invalidas].head(5).to_dict("records")
        raise ValueError(
            f"Hay {claves_invalidas.sum()} filas sin municipio o año válidos. "
            f"Ejemplos: {ejemplos}"
        )

    # Un Total vacío es un dato ausente legítimo y se conserva como nulo. En
    # cambio, cualquier texto no vacío que no sea numérico indica un error.
    totales_invalidos = total_normalizado.notna() & resultado["poblacion"].isna()
    if totales_invalidos.any():
        ejemplos = (
            df.loc[resultado.index[totales_invalidos], "Total"].head(5).tolist()
        )
        raise ValueError(
            f"Hay {totales_invalidos.sum()} valores de población no numéricos. "
            f"Ejemplos: {ejemplos}"
        )

    resultado = resultado.astype(
        {
            "codigo_ine": "string",
            "municipio": "string",
            "anio": "int16",
            # Int64 (con mayúscula) admite los valores ausentes del INE.
            "poblacion": "Int64",
        }
    )
    resultado["codigo_ine"] = resultado["codigo_ine"].str.zfill(5)

    claves_duplicadas = resultado.duplicated(
        subset=["codigo_ine", "anio"], keep=False
    )
    if claves_duplicadas.any():
        ejemplos = resultado.loc[claves_duplicadas].head(5).to_dict("records")
        raise ValueError(
            "La combinación codigo_ine-anio no es única. "
            f"Ejemplos: {ejemplos}"
        )

    return resultado.sort_values(["codigo_ine", "anio"]).reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    """Escribe el resultado con compresión Zstandard."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(ruta, index=False, engine="pyarrow", compression="zstd")


def main() -> None:
    df_raw = leer_datos()
    df_limpio = procesar_datos(df_raw)
    guardar_datos(df_limpio)

    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Años: {df_limpio['anio'].min()}-{df_limpio['anio'].max()}")
    print(f"Poblaciones ausentes: {df_limpio['poblacion'].isna().sum():,}")
    print(f"Salida: {RUTA_SALIDA}")


if __name__ == "__main__":
    main()
