import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL_INE = (
    "https://www.ine.es/dynt3/inebase/"
    "index.htm?capsel=5659&padre=7132"
)

CARPETA_RAW = Path("data/raw/ine_renta")
ARCHIVO_FINAL = CARPETA_RAW / "ine_renta_completa.csv"


def obtener_enlaces_provincias():
    respuesta = requests.get(URL_INE, timeout=60)
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")
    enlaces = []

    for enlace in soup.find_all("a", href=True):
        url = urljoin(URL_INE, enlace["href"])
        texto = enlace.get_text(strip=True)

        if "index.htm" in url and "capsel=" in url and texto:
            enlaces.append((texto, url))

    return enlaces


def obtener_id_tabla(url_provincia):
    respuesta = requests.get(url_provincia, timeout=60)
    respuesta.raise_for_status()

    soup = BeautifulSoup(respuesta.text, "html.parser")

    for enlace in soup.find_all("a", href=True):
        texto = enlace.get_text(" ", strip=True)

        if "Indicadores de renta media y mediana" in texto:
            url = enlace["href"]

            if "t=" in url:
                return url.split("t=")[1].split("&")[0]

    return None


def descargar_csv(id_tabla):
    url_csv = (
        "https://www.ine.es/jaxiT3/files/t/"
        f"csv_bdsc/{id_tabla}.csv"
    )

    respuesta = requests.get(url_csv, timeout=120)
    respuesta.raise_for_status()

    return pd.read_csv(
        BytesIO(respuesta.content),
        sep=";",
        encoding="utf-8-sig",
        dtype="string",
        low_memory=False,
    )


def main():
    CARPETA_RAW.mkdir(parents=True, exist_ok=True)

    provincias = obtener_enlaces_provincias()
    dataframes = []
    ids_descargados = set()

    for provincia, url in provincias:
        try:
            id_tabla = obtener_id_tabla(url)

            if id_tabla is None or id_tabla in ids_descargados:
                continue

            print(f"Descargando {provincia}: tabla {id_tabla}")

            df = descargar_csv(id_tabla)
            df["PROVINCIA_DESCARGA"] = provincia

            dataframes.append(df)
            ids_descargados.add(id_tabla)

            time.sleep(0.5)

        except Exception as error:
            print(f"Error en {provincia}: {error}")

    if not dataframes:
        print("No se ha descargado ningún archivo.")
        return

    df_final = pd.concat(dataframes, ignore_index=True)

    df_final.to_csv(
        ARCHIVO_FINAL,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print("\nDescarga terminada")
    print(f"Tablas descargadas: {len(ids_descargados)}")
    print(f"Filas totales: {len(df_final)}")
    print(f"Archivo: {ARCHIVO_FINAL}")


if __name__ == "__main__":
    main()