'''
Construye un dataset municipal integrado a partir de los Parquet procesados.

El catálogo del IGN define el universo de municipios. El resto de fuentes se
incorpora mediante LEFT JOIN por codigo_ine, por lo que una cobertura parcial
produce valores nulos sin eliminar municipios.
'''

import os
from pathlib import Path
import re
import unicodedata

import pandas as pd

try:
    from src.utils.procesamiento_funciones import (
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )
except ModuleNotFoundError:
    from procesamiento_funciones import (
        descargar_archivo_s3,
        guardar_parquet,
        subir_archivo_s3,
        validar_claves,
        validar_columnas,
    )


PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]
S3_KEY_SALIDA = "integrado/municipios.parquet"
RUTA_BASE = Path("/tmp/processed")
RUTA_SALIDA = Path("/tmp/integrado/municipios.parquet")

ARCHIVOS_ENTRADA = {
    "municipios": "ign/municipios.parquet",
    "catastro": "catastro/urbana.parquet",
    "catastro_2021": "catastro/urbana_2021.parquet",
    "edad": "ine_edad/edad.parquet",
    "migracion": "ine_migracion/migracion.parquet",
    "poblacion": "ine_poblacion/poblacion.parquet",
    "renta": "ine_renta/renta.parquet",
    "tamanio_hogar": "ine_tamanio_hogar/tamanio_hogar.parquet",
    "viviendas": "ine_viviendas/viviendas.parquet",
    "viviendas_turisticas": (
        "ine_viviendas_turisticas/viviendas_turisticas.parquet"
    ),
    "criminalidad": "mir_criminalidad/criminalidad.parquet",
    "distancia_costa": "mit/distancia_costa.parquet",
    "alquiler": "mivau_alquiler/alquiler.parquet",
    "transacciones": (
        "mivau_transacciones_municipales/transacciones_municipales.parquet"
    ),
    "transacciones_nuevas": (
        "mivau_transacciones_nuevas/transacciones_nuevas.parquet"
    ),
    "transacciones_segunda_mano": (
        "mivau_transacciones_segunda_mano/"
        "transacciones_segunda_mano.parquet"
    ),
    "paro": "sepe/paro.parquet",
}

COLUMNAS_CATASTRO_METRICAS = [
    "anio_ultima_revision",
    "inmuebles_urbanos",
    "valor_catastral_total_eur",
    "valor_catastral_suelo_eur",
    "superficie_urbana_m2",
    "parcelas_urbanas",
    "inmuebles_residenciales",
    "valor_catastral_residencial_eur",
    "valor_catastral_suelo_eur_m2",
    "valor_catastral_residencial_medio_eur",
]


def ruta_local(clave_s3: str) -> Path:
    return RUTA_BASE / Path(clave_s3)


def normalizar_codigo_ine(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    validar_columnas(df, ["codigo_ine"])
    resultado = df.copy()
    codigo = resultado["codigo_ine"].astype("string").str.strip()
    invalidos = codigo.notna() & ~codigo.str.fullmatch(r"\d{1,5}", na=False)
    if invalidos.any():
        ejemplos = codigo.loc[invalidos].head(5).tolist()
        raise ValueError(
            f"Hay códigos INE inválidos en {nombre}. Ejemplos: {ejemplos}"
        )
    resultado["codigo_ine"] = codigo.str.zfill(5)
    return resultado


def leer_parquet(nombre: str) -> pd.DataFrame:
    clave_s3 = ARCHIVOS_ENTRADA[nombre]
    ruta = ruta_local(clave_s3)
    descargar_archivo_s3(PROCESSED_BUCKET, clave_s3, ruta)
    datos = pd.read_parquet(ruta, engine="pyarrow")
    if datos.empty:
        raise ValueError(f"El dataset procesado {nombre} está vacío")
    return normalizar_codigo_ine(datos, nombre)


def seleccionar_ultimo_anio(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    validar_columnas(df, ["anio"])
    anios = pd.to_numeric(df["anio"], errors="coerce")
    if anios.dropna().empty:
        raise ValueError(f"No hay años válidos en {nombre}")
    anio = int(anios.max())
    resultado = df.loc[anios.eq(anio)].copy()
    resultado["anio"] = anio
    print(f"Año seleccionado en {nombre}: {anio}")
    return resultado


def preparar_municipios(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "codigo_ine",
        "municipio",
        "provincia",
        "capital",
        "poblacion",
        "superficie_km2",
        "densidad_poblacion_hab_km2",
        "longitud",
        "latitud",
    ]
    validar_columnas(df, columnas)
    resultado = df[columnas].rename(
        columns={"poblacion": "poblacion_ign"}
    )
    validar_claves(resultado, ["codigo_ine"], nombre="catálogo municipal")
    return resultado.sort_values("codigo_ine").reset_index(drop=True)


def preparar_unico(
    df: pd.DataFrame,
    nombre: str,
    *,
    renombres: dict = None,
    conservar_codigos_territoriales: bool = False,
) -> pd.DataFrame:
    columnas_identificacion = ["municipio", "provincia", "comunidad"]
    if not conservar_codigos_territoriales:
        columnas_identificacion.extend(
            ["codigo_provincia", "codigo_comunidad"]
        )
    resultado = df.drop(columns=columnas_identificacion, errors="ignore").copy()
    if renombres:
        resultado = resultado.rename(columns=renombres)
    validar_claves(resultado, ["codigo_ine"], nombre=nombre)
    return resultado


def preparar_catastro(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "codigo_ine",
        "anio",
        "codigo_comunidad",
        "comunidad",
        "codigo_provincia",
        *COLUMNAS_CATASTRO_METRICAS,
    ]
    validar_columnas(df, columnas)
    resultado = seleccionar_ultimo_anio(df[columnas], "catastro")
    resultado = resultado.rename(columns={"anio": "anio_catastro"})
    return preparar_unico(
        resultado,
        "catastro",
        conservar_codigos_territoriales=True,
    )


def preparar_catastro_2021(df: pd.DataFrame) -> pd.DataFrame:
    columnas = ["codigo_ine", "anio", *COLUMNAS_CATASTRO_METRICAS]
    validar_columnas(df, columnas)
    resultado = seleccionar_ultimo_anio(df[columnas], "catastro_2021")
    renombres = {
        "anio": "anio_catastro_2021",
        **{
            columna: f"{columna}_catastro_2021"
            for columna in COLUMNAS_CATASTRO_METRICAS
        },
    }
    return preparar_unico(
        resultado,
        "catastro_2021",
        renombres=renombres,
    )


def preparar_renta(df: pd.DataFrame) -> pd.DataFrame:
    resultado = seleccionar_ultimo_anio(df, "renta")
    return preparar_unico(
        resultado,
        "renta del último año",
        renombres={"anio": "anio_renta"},
    )


def nombre_columna_alquiler(fila: pd.Series) -> str:
    partes = [fila["elemento"], fila["tipo_vivienda"], fila["tipo_medida"]]
    texto = "_".join(str(parte).strip() for parte in partes)
    texto = unicodedata.normalize("NFKD", texto).encode(
        "ascii", "ignore"
    ).decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto).strip("_").lower()
    return f"alquiler_{texto}"


def preparar_alquiler(df: pd.DataFrame) -> pd.DataFrame:
    dimensiones = ["elemento", "tipo_vivienda", "tipo_medida"]
    columnas = ["codigo_ine", "anio", *dimensiones, "valor"]
    validar_columnas(df, columnas)
    resultado = seleccionar_ultimo_anio(df[columnas], "alquiler")
    anio = int(resultado["anio"].iat[0])
    resultado["variable"] = resultado.apply(
        nombre_columna_alquiler, axis="columns"
    )

    combinaciones = resultado[[*dimensiones, "variable"]].drop_duplicates()
    colisiones = combinaciones.duplicated("variable", keep=False)
    if colisiones.any():
        ejemplos = combinaciones.loc[colisiones].head(10).to_dict("records")
        raise ValueError(
            "Varias combinaciones de alquiler generan la misma columna. "
            f"Ejemplos: {ejemplos}"
        )

    validar_claves(
        resultado,
        ["codigo_ine", "variable"],
        nombre="alquiler municipal del último año",
    )
    resultado = resultado.pivot(
        index="codigo_ine", columns="variable", values="valor"
    ).reset_index()
    resultado.columns.name = None
    resultado.insert(1, "anio_alquiler", anio)
    validar_claves(resultado, ["codigo_ine"], nombre="alquiler pivotado")
    return resultado


def unir_dataset(
    base: pd.DataFrame,
    datos: pd.DataFrame,
    nombre: str,
) -> pd.DataFrame:
    validar_claves(datos, ["codigo_ine"], nombre=nombre)
    solapadas = set(base.columns).intersection(datos.columns) - {"codigo_ine"}
    if solapadas:
        raise ValueError(
            f"Hay columnas repetidas al incorporar {nombre}: "
            f"{sorted(solapadas)}"
        )

    municipios_con_datos = base["codigo_ine"].isin(datos["codigo_ine"]).sum()
    resultado = base.merge(
        datos,
        on="codigo_ine",
        how="left",
        validate="one_to_one",
    )
    if len(resultado) != len(base):
        raise ValueError(f"El join de {nombre} ha alterado el número de filas")
    print(
        f"Cobertura de {nombre}: {municipios_con_datos:,}/{len(base):,} "
        "municipios"
    )
    return resultado


def calcular_variables(df: pd.DataFrame) -> pd.DataFrame:
    resultado = df.copy()
    validar_columnas(
        resultado,
        [
            "poblacion_2025",
            "variacion_poblacion_1_anio",
            "saldo_interior",
            "saldo_exterior",
            "viviendas_turisticas",
            "paro_medio_2025",
            "superficie_km2",
            "superficie_urbana_m2",
            "anio_catastro",
            "anio_catastro_2021",
            "inmuebles_residenciales",
            "inmuebles_residenciales_catastro_2021",
            "valor_catastral_residencial_medio_eur",
            "valor_catastral_residencial_medio_eur_catastro_2021",
            "superficie_urbana_m2_catastro_2021",
            "valor_catastral_suelo_eur_m2",
            "valor_catastral_suelo_eur_m2_catastro_2021",
        ],
    )

    anios_catastro = set(
        resultado["anio_catastro"].dropna().astype("int64").unique()
    )
    anios_catastro_2021 = set(
        resultado["anio_catastro_2021"].dropna().astype("int64").unique()
    )
    if anios_catastro != {2026} or anios_catastro_2021 != {2021}:
        raise ValueError(
            "Los periodos del Catastro no forman el intervalo 2021-2026. "
            f"Años actuales: {sorted(anios_catastro)}; "
            f"años de referencia: {sorted(anios_catastro_2021)}"
        )

    # Los saldos migratorios son de 2024. La población de ese mismo año se
    # reconstruye a partir de la población de 2025 y su variación anual:
    # variacion_poblacion_1_anio = poblacion_2025 - poblacion_2024.
    poblacion_2024 = (
        resultado["poblacion_2025"]
        - resultado["variacion_poblacion_1_anio"]
    ).where(lambda valores: valores.gt(0))

    resultado["saldo_interior_por_1000_habitantes"] = (
        resultado["saldo_interior"] / poblacion_2024 * 1_000
    ).round(2).astype("Float64")
    resultado["saldo_exterior_por_1000_habitantes"] = (
        resultado["saldo_exterior"] / poblacion_2024 * 1_000
    ).round(2).astype("Float64")

    # El último periodo turístico disponible es 2026M05. Al no disponer de
    # población de 2026, se utiliza la población de 2025 como aproximación.
    poblacion_2025_valida = resultado["poblacion_2025"].where(
        resultado["poblacion_2025"].gt(0)
    )
    resultado["viviendas_turisticas_por_1000_habitantes"] = (
        resultado["viviendas_turisticas"] / poblacion_2025_valida * 1_000
    ).round(2).astype("Float64")
    resultado["paro_por_1000_habitantes"] = (
        resultado["paro_medio_2025"] / poblacion_2025_valida * 1_000
    ).round(2).astype("Float64")

    # La superficie municipal del IGN está expresada en km2 y la superficie
    # urbana del Catastro en m2; 1 km2 equivale a 1.000.000 m2.
    superficie_municipal_m2 = (
        resultado["superficie_km2"] * 1_000_000
    ).where(lambda valores: valores.gt(0))
    resultado["porcentaje_superficie_urbana"] = (
        resultado["superficie_urbana_m2"]
        / superficie_municipal_m2
        * 100
    ).round(2).astype("Float64")

    # Variaciones absolutas del Catastro entre 2021 y 2026.
    resultado["variacion_inmuebles_residenciales_5_anios"] = (
        resultado["inmuebles_residenciales"]
        - resultado["inmuebles_residenciales_catastro_2021"]
    ).astype("Int64")
    resultado[
        "variacion_valor_catastral_residencial_medio_eur_5_anios"
    ] = (
        resultado["valor_catastral_residencial_medio_eur"]
        - resultado[
            "valor_catastral_residencial_medio_eur_catastro_2021"
        ]
    ).round(2).astype("Float64")
    resultado["variacion_superficie_urbana_m2_5_anios"] = (
        resultado["superficie_urbana_m2"]
        - resultado["superficie_urbana_m2_catastro_2021"]
    ).astype("Int64")
    resultado[
        "variacion_valor_catastral_suelo_eur_m2_5_anios"
    ] = (
        resultado["valor_catastral_suelo_eur_m2"]
        - resultado["valor_catastral_suelo_eur_m2_catastro_2021"]
    ).round(2).astype("Float64")

    # El Catastro actual es de 2026 y la población más reciente disponible es
    # de 2025. Se usa esta última como aproximación para expresar tanto el
    # stock residencial como su incremento 2021-2026 por habitante actual.
    resultado["inmuebles_residenciales_por_1000_habitantes"] = (
        resultado["inmuebles_residenciales"]
        / poblacion_2025_valida
        * 1_000
    ).round(2).astype("Float64")
    resultado[
        "variacion_inmuebles_residenciales_5_anios_por_1000_habitantes"
    ] = (
        resultado["variacion_inmuebles_residenciales_5_anios"]
        / poblacion_2025_valida
        * 1_000
    ).round(2).astype("Float64")
    return resultado


def preparar_dataset(nombre: str, df: pd.DataFrame) -> pd.DataFrame:
    if nombre == "catastro":
        return preparar_catastro(df)
    if nombre == "catastro_2021":
        return preparar_catastro_2021(df)
    if nombre == "renta":
        return preparar_renta(df)
    if nombre == "alquiler":
        return preparar_alquiler(df)
    if nombre == "migracion":
        return preparar_unico(
            df,
            nombre,
            renombres={"anio": "anio_migracion"},
        )
    if nombre == "criminalidad":
        return preparar_unico(
            df,
            nombre,
            renombres={"anio": "anio_criminalidad"},
        )
    if nombre == "viviendas_turisticas":
        return preparar_unico(
            df,
            nombre,
            renombres={
                "periodo": "periodo_viviendas_turisticas",
                "anio": "anio_viviendas_turisticas",
                "mes": "mes_viviendas_turisticas",
            },
        )
    return preparar_unico(df, nombre)


def procesar_datos(datos: dict) -> pd.DataFrame:
    faltantes = set(ARCHIVOS_ENTRADA).difference(datos)
    if faltantes:
        raise ValueError(
            f"Faltan datasets para el join: {sorted(faltantes)}"
        )
    resultado = preparar_municipios(datos["municipios"])

    for nombre in ARCHIVOS_ENTRADA:
        if nombre == "municipios":
            continue
        dataset = preparar_dataset(nombre, datos[nombre])
        resultado = unir_dataset(resultado, dataset, nombre)

    resultado = calcular_variables(resultado)
    validar_claves(
        resultado,
        ["codigo_ine"],
        nombre="dataset municipal integrado",
    )
    return resultado.sort_values("codigo_ine").reset_index(drop=True)


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    resultado = preparar_municipios(leer_parquet("municipios"))
    for nombre in ARCHIVOS_ENTRADA:
        if nombre == "municipios":
            continue
        dataset = preparar_dataset(nombre, leer_parquet(nombre))
        resultado = unir_dataset(resultado, dataset, nombre)

    resultado = calcular_variables(resultado)
    validar_claves(
        resultado,
        ["codigo_ine"],
        nombre="dataset municipal integrado",
    )
    resultado = resultado.sort_values("codigo_ine").reset_index(drop=True)
    guardar_datos(resultado)
    salida_s3 = subir_archivo_s3(
        RUTA_SALIDA,
        PROCESSED_BUCKET,
        S3_KEY_SALIDA,
    )
    print(f"Municipios guardados: {len(resultado):,}")
    print(f"Columnas guardadas: {len(resultado.columns):,}")
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
