from pathlib import Path

import requests


def descargar_archivo(
    url: str,
    ruta_salida: Path,
    timeout: int = 180,
) -> Path:
    """
    Descarga un archivo desde una URL y lo guarda localmente.

    Parameters
    ----------
    url:
        Dirección del archivo.
    ruta_salida:
        Ruta local donde se guardará.
    timeout:
        Tiempo máximo de espera en segundos.

    Returns
    -------
    Path
        Ruta del archivo descargado.
    """
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=timeout) as respuesta:
        respuesta.raise_for_status()

        with ruta_salida.open("wb") as archivo:
            for bloque in respuesta.iter_content(
                chunk_size=1024 * 1024
            ):
                if bloque:
                    archivo.write(bloque)

    if not ruta_salida.exists() or ruta_salida.stat().st_size == 0:
        raise ValueError(
            f"El archivo descargado está vacío: {url}"
        )

    tamaño_mb = ruta_salida.stat().st_size / 1024 / 1024

    print(
        f"Archivo descargado correctamente: {ruta_salida} "
        f"({tamaño_mb:.2f} MB)"
    )

    return ruta_salida