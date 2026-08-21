from pathlib import Path

from src.utils.descargar_archivo import descargar_archivo


URL = (
    "https://cdn.mivau.gob.es/portal-web-mivau/"
    "Datos_MIVAU/CSV/VDP001_01.csv"
)

RUTA_SALIDA = Path(
    "data/raw/mivau/alquiler.csv"
)


def main() -> None:
    descargar_archivo(
        url=URL,
        ruta_salida=RUTA_SALIDA,
    )


if __name__ == "__main__":
    main()