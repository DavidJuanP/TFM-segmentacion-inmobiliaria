from pathlib import Path

import pandas as pd


RUTA_ENTRADA = Path(
    "data/raw/ine/poblacion.csv"
)

RUTA_SALIDA = Path(
    "data/processed/ine/poblacion.parquet"
)


def leer_datos() -> pd.DataFrame:
    df = pd.read_csv(
        RUTA_ENTRADA,
        sep=";",
        encoding="utf-8",
        dtype=str,
    )

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    return df


def obtener_columna(
    df: pd.DataFrame,
    posibles_nombres: list[str],
) -> str:
    for nombre in posibles_nombres:
        if nombre in df.columns:
            return nombre

    raise ValueError(
        "No se ha encontrado ninguna de estas columnas: "
        f"{posibles_nombres}\n\n"
        f"Columnas disponibles:\n{df.columns.tolist()}"
    )


def procesar_datos(
    df: pd.DataFrame,
) -> pd.DataFrame:
    columna_municipio = obtener_columna(
        df,
        [
            "municipios",
            "municipio",
        ],
    )

    columna_periodo = obtener_columna(
        df,
        [
            "periodo",
            "año",
            "anio",
        ],
    )

    columna_valor = obtener_columna(
        df,
        [
            "total",
            "valor",
        ],
    )

    resultado = df[
        [
            columna_municipio,
            columna_periodo,
            columna_valor,
        ]
    ].copy()

    # El INE suele incluir el código municipal
    # al principio del nombre:
    # "28079 Madrid"
    resultado["codigo_ine"] = (
        resultado[columna_municipio]
        .str.extract(r"^(\d{5})", expand=False)
    )

    resultado["municipio"] = (
        resultado[columna_municipio]
        .str.replace(
            r"^\d{5}\s+",
            "",
            regex=True,
        )
        .str.strip()
    )

    resultado["anio"] = pd.to_numeric(
        resultado[columna_periodo],
        errors="coerce",
    )

    resultado["poblacion"] = (
        resultado[columna_valor]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    resultado["poblacion"] = pd.to_numeric(
        resultado["poblacion"],
        errors="coerce",
    )

    resultado = resultado[
        [
            "codigo_ine",
            "municipio",
            "anio",
            "poblacion",
        ]
    ]

    resultado = resultado.dropna(
        subset=[
            "codigo_ine",
            "anio",
            "poblacion",
        ]
    )

    resultado["codigo_ine"] = (
        resultado["codigo_ine"]
        .astype(str)
        .str.zfill(5)
    )

    resultado["anio"] = (
        resultado["anio"]
        .astype(int)
    )

    resultado["poblacion"] = (
        resultado["poblacion"]
        .astype(int)
    )

    resultado = resultado.drop_duplicates(
        subset=[
            "codigo_ine",
            "anio",
        ]
    )

    resultado = resultado.sort_values(
        [
            "codigo_ine",
            "anio",
        ]
    )

    return resultado.reset_index(drop=True)


def guardar_datos(
    df: pd.DataFrame,
) -> None:
    RUTA_SALIDA.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        RUTA_SALIDA,
        index=False,
    )


def main() -> None:
    df_raw = leer_datos()

    print(
        f"Filas raw: {len(df_raw):,}"
    )

    df = procesar_datos(df_raw)

    print(
        f"Filas processed: {len(df):,}"
    )

    print(
        f"Municipios: {df['codigo_ine'].nunique():,}"
    )

    print(
        f"Años: {df['anio'].min()} - {df['anio'].max()}"
    )

    print("\nPrimeras filas:")
    print(df.head())

    guardar_datos(df)

    print(
        f"\nGuardado en: {RUTA_SALIDA}"
    )


if __name__ == "__main__":
    main()