'''
Calcula las transacciones municipales de 2025 y sus variaciones a 1, 3 y 5 años.

'''

import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

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
S3_KEY_ENTRADA = "mivau/transacciones_municipales.xls"
S3_KEY_CATALOGO = "ign/municipios.xlsx"
S3_KEY_ALIAS = "mivau/alquiler.csv"
S3_KEY_SALIDA = "mivau/transacciones_municipales.parquet"
RUTA_ENTRADA = Path("/tmp/raw/mivau/transacciones_municipales.xls")
RUTA_CATALOGO = Path("/tmp/raw/ign/municipios.xlsx")
RUTA_ALIAS = Path("/tmp/raw/mivau/alquiler.csv")
RUTA_SALIDA = Path(
    "/tmp/processed/mivau/transacciones_municipales.parquet"
)

FILA_ANIOS = 10
FILA_TRIMESTRES = 12
FILA_INICIO_DATOS = 13
COLUMNA_TERRITORIO = 1
PRIMERA_COLUMNA_VALORES = 3
HOJA_CATALOGO = "IGN_INFOGEO_MUNICIPIOS"
COLUMNAS_CATALOGO = {"Identificador", "Nombre", "Provincia"}
COLUMNAS_ALIAS = {"COD_POSTAL", "NOMBRE_MUNICIPIO", "PROVINCIA"}
ANIO_REFERENCIA = 2025
ANIO_DESCARTADO = 2026
TRIMESTRES_ANIO = 4
HORIZONTES = {
    1: 2024,
    3: 2022,
    5: 2020,
}
COMUNIDADES_UNIPROVINCIALES = {
    "asturias principado de": "Asturias",
    "balears illes": "Balears, Illes",
    "cantabria": "Cantabria",
    "madrid comunidad de": "Madrid",
    "murcia region de": "Murcia",
    "navarra comunidad foral de": "Navarra",
    "rioja la": "Rioja, La",
}
ALIAS_CODIGOS_INE = {
    "Palma de Mallorca": "07040",
    "Manjabálago": "05119",
    "Castrillo Matajudíos": "09090",
    "Villarcayo de Merindad de Castilla la Vi": "09903",
    "Villadecanes": "24206",
    "San Ildefonso": "40181",
    "Corrales": "49054",
    "Puebla de Don Francisco": "16173",
    "Cruïlles, Monells i Sant Sadurní de l'He": "17901",
    "Adsubia": "03001",
    "Alcocer de Planes": "03007",
    "Facheca": "03067",
    "Fondó de les Neus (el)": "03077",
    "San Vicente del Raspeig/Sant Vicent del": "03122",
    "Vall de Gallinera": "03136",
    "Castellón de la Plana/Castelló de la Pla": "12040",
    "Alfara de Algimia": "46024",
    "Masalavés": "46162",
    "Sant Joan de l'Énova": "46222",
    "Guadiana del Caudillo": "06903",
    "Higuera": "10097",
    "Oza-Cesuras * Unión de municipios Oza y Cesuras": "15902",
    "Gargantilla del Lozoya y Pinilla de Buit": "28063",
    "Abárzuza": "31002",
    "Allín": "31011",
    "Atez": "31040",
    "Barañain": "31901",
    "Berrioplano": "31902",
    "Castillonuevo": "31071",
    "Ciriza": "31075",
    "Echarri": "31083",
    "Egüés": "31086",
    "Gallipienzo": "31110",
    "Juslapeña": "31136",
    "Leache": "31146",
    "Lizoáin-Arriasgoiti": "31156",
    "Monreal": "31172",
    "Navascués": "31181",
    "Oitz": "31187",
    "Ollo": "31194",
    "Orbaitzeta": "31195",
    "Pueyo": "31207",
    "Romanzado": "31209",
    "Ujué": "31235",
    "Unzué": "31238",
    "Urrotz": "31244",
    "Arrazua-Ubarrundia": "01008",
    "Legutiano": "01058",
    "Moreda de Álava": "01039",
    "Ribera Baja/Erribera Beitia": "01047",
    "Bidegoian": "20024",
    "Arrankudiaga": "48009",
    "Sopelana": "48085",
    "Lumbreras": "26091",
}


def normalizar_texto(valor: object, *, ordenar: bool = False) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(car for car in texto if not unicodedata.combining(car))
    palabras = re.findall(r"[a-z0-9]+", texto.casefold())
    if ordenar:
        palabras.sort()
    return " ".join(palabras)


def normalizar_municipio(valor: object) -> str:
    palabras = normalizar_texto(valor).split()
    articulos = {"el", "la", "los", "las", "els", "les", "l"}
    if len(palabras) > 1 and palabras[-1] in articulos:
        palabras.insert(0, palabras.pop())
    return " ".join(palabras)


def leer_datos(ruta: Path = RUTA_ENTRADA) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de entrada: {ruta}")
    return pd.read_excel(ruta, sheet_name=0, header=None, engine="xlrd")


def leer_catalogo_municipios(
    ruta: Path = RUTA_CATALOGO,
) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el catálogo municipal: {ruta}")
    df = pd.read_excel(
        ruta,
        sheet_name=HOJA_CATALOGO,
        dtype="string",
    )
    validar_columnas(df, COLUMNAS_CATALOGO)
    return df


def leer_alias_municipios(ruta: Path = RUTA_ALIAS) -> pd.DataFrame:
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero de alias municipales: {ruta}")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string")
    validar_columnas(df, COLUMNAS_ALIAS)
    return df


def extraer_periodos(df: pd.DataFrame) -> pd.DataFrame:
    columnas = list(range(PRIMERA_COLUMNA_VALORES, df.shape[1]))
    anios = (
        df.iloc[FILA_ANIOS, PRIMERA_COLUMNA_VALORES:]
        .ffill()
        .astype("string")
        .str.extract(r"(\d{4})", expand=False)
    )
    etiquetas_trimestre = df.iloc[
        FILA_TRIMESTRES, PRIMERA_COLUMNA_VALORES:
    ].astype("string")
    trimestres = etiquetas_trimestre.str.extract(r"([1-4])", expand=False)
    periodos = pd.DataFrame(
        {
            "columna_origen": columnas,
            "anio": pd.to_numeric(anios, errors="coerce").array,
            "trimestre": pd.to_numeric(trimestres, errors="coerce").array,
            "provisional": etiquetas_trimestre.str.contains(
                "(*)", regex=False, na=False
            ).array,
        }
    )
    if periodos[["anio", "trimestre"]].isna().any(axis=None):
        raise ValueError("No se han podido interpretar todos los periodos del XLS")
    validar_claves(
        periodos,
        ["anio", "trimestre"],
        nombre="cabecera temporal de transacciones municipales",
    )
    return periodos


def extraer_municipios(
    df: pd.DataFrame,
    catalogo_municipios: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    provincias_catalogo = set()
    if catalogo_municipios is not None:
        validar_columnas(catalogo_municipios, COLUMNAS_CATALOGO)
        provincias_catalogo = set(
            catalogo_municipios["Provincia"]
            .dropna()
            .map(lambda valor: normalizar_texto(valor, ordenar=True))
        )

    filas = []
    comunidad = None
    provincia = None
    valores = df.iloc[FILA_INICIO_DATOS:, PRIMERA_COLUMNA_VALORES:]
    tiene_datos = valores.notna().any(axis="columns")

    for indice, es_municipio in tiene_datos.items():
        valor = df.iat[indice, COLUMNA_TERRITORIO]
        if pd.isna(valor):
            continue
        territorio = str(valor).strip()
        territorio_normalizado = normalizar_texto(territorio)
        es_ciudad_autonoma = territorio_normalizado in {"ceuta", "melilla"}

        # En los ficheros de vivienda nueva y de segunda mano algunos
        # agregados provinciales y autonómicos tienen cifras. No deben
        # confundirse con municipios: las comunidades aparecen en mayúsculas
        # y las provincias se identifican mediante el catálogo del IGN.
        if territorio == territorio.upper() and not es_ciudad_autonoma:
            comunidad = territorio
            provincia = COMUNIDADES_UNIPROVINCIALES.get(
                territorio_normalizado
            )
            continue
        clave_territorio = normalizar_texto(territorio, ordenar=True)
        clave_provincia_actual = (
            normalizar_texto(provincia, ordenar=True)
            if provincia is not None
            else None
        )
        if (
            not es_ciudad_autonoma
            and clave_territorio in provincias_catalogo
            and clave_territorio != clave_provincia_actual
        ):
            provincia = territorio
            continue

        if not es_municipio:
            if territorio == territorio.upper():
                comunidad = territorio
                provincia = COMUNIDADES_UNIPROVINCIALES.get(
                    territorio_normalizado
                )
            else:
                provincia = territorio
            continue

        if es_ciudad_autonoma:
            comunidad = territorio
            provincia = territorio
        if comunidad is None or provincia is None:
            raise ValueError(
                f"No se pudo determinar el territorio de {territorio!r}"
            )
        filas.append(
            {
                "fila_origen": indice,
                "comunidad": comunidad,
                "provincia_origen": provincia,
                "municipio_origen": territorio,
            }
        )

    if not filas:
        raise ValueError("No se han encontrado municipios en el XLS")
    return pd.DataFrame(filas)


def preparar_catalogo(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_CATALOGO)
    catalogo = df[["Identificador", "Nombre", "Provincia"]].copy().rename(
        columns={
            "Identificador": "codigo_ine",
            "Nombre": "municipio",
            "Provincia": "provincia",
        }
    )
    catalogo["codigo_ine"] = catalogo["codigo_ine"].str.strip().str.zfill(5)
    catalogo["clave_provincia"] = catalogo["provincia"].map(
        lambda valor: normalizar_texto(valor, ordenar=True)
    )
    catalogo["clave_municipio"] = catalogo["municipio"].map(
        normalizar_municipio
    )
    catalogo["clave_municipio_flexible"] = catalogo["municipio"].map(
        lambda valor: normalizar_texto(valor, ordenar=True)
    )
    validar_claves(catalogo, ["codigo_ine"], nombre="catálogo municipal")
    validar_claves(
        catalogo,
        ["clave_provincia", "clave_municipio"],
        nombre="nombres normalizados del catálogo municipal",
    )
    return catalogo


def preparar_aliases(df: pd.DataFrame) -> pd.DataFrame:
    validar_columnas(df, COLUMNAS_ALIAS)
    aliases = df[list(COLUMNAS_ALIAS)].drop_duplicates().copy().rename(
        columns={
            "COD_POSTAL": "codigo_ine",
            "NOMBRE_MUNICIPIO": "municipio",
            "PROVINCIA": "provincia",
        }
    )
    aliases["codigo_ine"] = aliases["codigo_ine"].str.strip().str.zfill(5)
    aliases["clave_provincia"] = aliases["provincia"].map(
        lambda valor: normalizar_texto(valor, ordenar=True)
    )
    aliases["clave_municipio"] = aliases["municipio"].map(
        normalizar_municipio
    )
    aliases["clave_municipio_flexible"] = aliases["municipio"].map(
        lambda valor: normalizar_texto(valor, ordenar=True)
    )
    return aliases[
        [
            "codigo_ine",
            "clave_provincia",
            "clave_municipio",
            "clave_municipio_flexible",
        ]
    ].drop_duplicates()


def asignar_codigos_ine(
    municipios: pd.DataFrame,
    catalogo_raw: pd.DataFrame,
    alias_raw: pd.DataFrame,
) -> pd.DataFrame:
    municipios = municipios.copy()
    municipios["clave_provincia"] = municipios["provincia_origen"].map(
        lambda valor: normalizar_texto(valor, ordenar=True)
    )
    municipios["clave_municipio"] = municipios["municipio_origen"].map(
        normalizar_municipio
    )
    municipios["clave_municipio_flexible"] = municipios[
        "municipio_origen"
    ].map(lambda valor: normalizar_texto(valor, ordenar=True))
    catalogo = preparar_catalogo(catalogo_raw)
    referencias = pd.concat(
        [
            catalogo[
                [
                    "codigo_ine",
                    "clave_provincia",
                    "clave_municipio",
                    "clave_municipio_flexible",
                ]
            ],
            preparar_aliases(alias_raw),
        ],
        ignore_index=True,
    ).drop_duplicates()
    claves_nombre = ["clave_provincia", "clave_municipio"]
    conflictos = referencias.groupby(claves_nombre)["codigo_ine"].nunique().gt(1)
    if conflictos.any():
        ejemplos = conflictos.loc[conflictos].head(10).index.tolist()
        raise ValueError(
            "Hay nombres municipales asociados a varios códigos INE. "
            f"Ejemplos: {ejemplos}"
        )
    referencias = referencias.drop_duplicates(claves_nombre)
    resultado = municipios.merge(
        referencias[[*claves_nombre, "codigo_ine"]],
        on=claves_nombre,
        how="left",
        validate="one_to_one",
    )
    alias_explicitos = {
        normalizar_municipio(nombre): codigo
        for nombre, codigo in ALIAS_CODIGOS_INE.items()
    }
    resultado["codigo_ine"] = resultado["codigo_ine"].fillna(
        resultado["clave_municipio"].map(alias_explicitos)
    )
    claves_flexibles = ["clave_provincia", "clave_municipio_flexible"]
    referencias_flexibles = referencias.loc[
        referencias.groupby(claves_flexibles)["codigo_ine"].transform(
            "nunique"
        ).eq(1)
    ].drop_duplicates(claves_flexibles)
    resultado = resultado.merge(
        referencias_flexibles[
            [*claves_flexibles, "codigo_ine"]
        ].rename(columns={"codigo_ine": "codigo_ine_flexible"}),
        on=claves_flexibles,
        how="left",
        validate="many_to_one",
    )
    resultado["codigo_ine"] = resultado["codigo_ine"].fillna(
        resultado.pop("codigo_ine_flexible")
    )
    sin_codigo = resultado["codigo_ine"].isna()
    if sin_codigo.any():
        ejemplos = resultado.loc[
            sin_codigo, ["provincia_origen", "municipio_origen"]
        ].head(10).to_dict("records")
        raise ValueError(
            f"No se encontró código INE para {sin_codigo.sum()} municipios. "
            f"Ejemplos: {ejemplos}"
        )
    resultado = resultado.merge(
        catalogo[["codigo_ine", "municipio", "provincia"]],
        on="codigo_ine",
        how="left",
        validate="many_to_one",
    )
    return resultado


def procesar_datos(
    df: pd.DataFrame,
    catalogo_municipios: pd.DataFrame,
    alias_municipios: pd.DataFrame,
) -> pd.DataFrame:
    if df.shape[0] <= FILA_INICIO_DATOS or df.shape[1] <= PRIMERA_COLUMNA_VALORES:
        raise ValueError(f"El XLS no tiene la estructura esperada: {df.shape}")

    periodos = extraer_periodos(df)
    municipios = asignar_codigos_ine(
        extraer_municipios(df, catalogo_municipios),
        catalogo_municipios,
        alias_municipios,
    )
    columnas_valores = periodos["columna_origen"].tolist()
    valores = df.loc[municipios["fila_origen"], columnas_valores].copy()
    valores.index = municipios["fila_origen"].to_numpy()
    valores.columns = columnas_valores
    valores = valores.rename_axis("fila_origen").reset_index().melt(
        id_vars="fila_origen",
        var_name="columna_origen",
        value_name="numero_transacciones",
    )

    resultado = valores.merge(
        municipios[
            [
                "fila_origen",
                "codigo_ine",
                "municipio",
                "provincia",
                "comunidad",
            ]
        ],
        on="fila_origen",
        how="left",
        validate="many_to_one",
    ).merge(
        periodos,
        on="columna_origen",
        how="left",
        validate="many_to_one",
    )
    resultado["codigo_provincia"] = resultado["codigo_ine"].str[:2]
    resultado["numero_transacciones"] = convertir_numero_es(
        resultado["numero_transacciones"],
        "número de transacciones",
        entero=True,
        decimal_coma=False,
    )
    resultado = resultado.astype(
        {"anio": "int16", "trimestre": "int8", "provisional": "boolean"}
    )
    claves = ["codigo_ine", "anio", "trimestre"]
    valores_solapados = resultado.groupby(claves)[
        "numero_transacciones"
    ].count().gt(1)
    if valores_solapados.any():
        ejemplos = valores_solapados.loc[valores_solapados].head(10).index.tolist()
        raise ValueError(
            "Hay varias cifras publicadas para el mismo municipio y periodo. "
            f"Ejemplos: {ejemplos}"
        )

    resultado = resultado.groupby(
        [
            "codigo_ine",
            "municipio",
            "codigo_provincia",
            "provincia",
            "comunidad",
            "anio",
            "trimestre",
        ],
        as_index=False,
        dropna=False,
    ).agg(
        provisional=("provisional", "max"),
        numero_transacciones=(
            "numero_transacciones",
            lambda valores: valores.sum(min_count=1),
        ),
    )
    for columna in ["municipio", "provincia", "comunidad"]:
        resultado[columna] = resultado[columna].astype("string")

    # El año 2026 solo contiene datos parciales y no debe convertirse en un
    # total anual. Un total solo es válido si sus cuatro trimestres tienen dato.
    resultado = resultado.loc[resultado["anio"].ne(ANIO_DESCARTADO)].copy()
    anios_necesarios = {ANIO_REFERENCIA, *HORIZONTES.values()}
    anios_ausentes = anios_necesarios.difference(resultado["anio"].unique())
    if anios_ausentes:
        raise ValueError(
            "Faltan años necesarios para calcular las variaciones de "
            f"transacciones: {sorted(anios_ausentes)}"
        )

    identificadores = [
        "codigo_ine",
        "municipio",
        "codigo_provincia",
        "provincia",
        "comunidad",
    ]
    totales_anuales = (
        resultado.loc[resultado["anio"].isin(anios_necesarios)]
        .groupby(
            [*identificadores, "anio"],
            as_index=False,
            dropna=False,
        )
        .agg(
            numero_transacciones=(
                "numero_transacciones",
                lambda valores: valores.sum(min_count=TRIMESTRES_ANIO),
            ),
            trimestres=("trimestre", "nunique"),
        )
    )
    periodos_incompletos = totales_anuales["trimestres"].ne(TRIMESTRES_ANIO)
    if periodos_incompletos.any():
        ejemplos = totales_anuales.loc[
            periodos_incompletos, ["codigo_ine", "anio", "trimestres"]
        ].head(10).to_dict("records")
        raise ValueError(
            "Hay municipios sin los cuatro trimestres necesarios para "
            f"calcular el total anual. Ejemplos: {ejemplos}"
        )
    totales_anuales = totales_anuales.drop(columns="trimestres")
    validar_claves(
        totales_anuales,
        ["codigo_ine", "anio"],
        nombre="transacciones municipales anuales",
    )

    transacciones_referencia = totales_anuales.loc[
        totales_anuales["anio"].eq(ANIO_REFERENCIA),
        [*identificadores, "numero_transacciones"],
    ].rename(columns={"numero_transacciones": "transacciones_2025"})
    validar_claves(
        transacciones_referencia,
        ["codigo_ine"],
        nombre=f"transacciones municipales de {ANIO_REFERENCIA}",
    )

    for numero_anios, anio_anterior in HORIZONTES.items():
        columna_anterior = f"transacciones_{anio_anterior}"
        columna_variacion = (
            f"variacion_transacciones_{numero_anios}_anio"
            if numero_anios == 1
            else f"variacion_transacciones_{numero_anios}_anios"
        )
        transacciones_anteriores = totales_anuales.loc[
            totales_anuales["anio"].eq(anio_anterior),
            ["codigo_ine", "numero_transacciones"],
        ].rename(columns={"numero_transacciones": columna_anterior})
        transacciones_referencia = transacciones_referencia.merge(
            transacciones_anteriores,
            on="codigo_ine",
            how="left",
            validate="one_to_one",
        )
        transacciones_referencia[columna_variacion] = (
            transacciones_referencia["transacciones_2025"]
            - transacciones_referencia.pop(columna_anterior)
        ).astype("Int64")

    columnas = [
        *identificadores,
        "transacciones_2025",
        "variacion_transacciones_1_anio",
        "variacion_transacciones_3_anios",
        "variacion_transacciones_5_anios",
    ]
    transacciones_referencia = transacciones_referencia[columnas]
    validar_claves(
        transacciones_referencia,
        ["codigo_ine"],
        nombre="variaciones de transacciones municipales",
    )
    return transacciones_referencia.sort_values("codigo_ine").reset_index(
        drop=True
    )


def guardar_datos(df: pd.DataFrame, ruta: Path = RUTA_SALIDA) -> None:
    guardar_parquet(df, ruta)


def main() -> None:
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ENTRADA, RUTA_ENTRADA)
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_CATALOGO, RUTA_CATALOGO)
    descargar_archivo_s3(RAW_BUCKET, S3_KEY_ALIAS, RUTA_ALIAS)
    df_raw = leer_datos()
    catalogo = leer_catalogo_municipios()
    aliases = leer_alias_municipios()
    df_limpio = procesar_datos(df_raw, catalogo, aliases)
    guardar_datos(df_limpio)
    salida_s3 = subir_archivo_s3(
        RUTA_SALIDA, PROCESSED_BUCKET, S3_KEY_SALIDA
    )
    print(f"Filas leídas: {len(df_raw):,}")
    print(f"Municipios: {df_limpio['codigo_ine'].nunique():,}")
    print(f"Filas guardadas: {len(df_limpio):,}")
    print(f"Año de referencia: {ANIO_REFERENCIA}")
    print(
        "Transacciones de 2025 ausentes: "
        f"{df_limpio['transacciones_2025'].isna().sum():,}"
    )
    for numero_anios in HORIZONTES:
        sufijo = "anio" if numero_anios == 1 else "anios"
        columna = f"variacion_transacciones_{numero_anios}_{sufijo}"
        print(
            f"Variaciones a {numero_anios} año(s) ausentes: "
            f"{df_limpio[columna].isna().sum():,}"
        )
    print(f"Salida: {salida_s3}")


if __name__ == "__main__":
    main()
