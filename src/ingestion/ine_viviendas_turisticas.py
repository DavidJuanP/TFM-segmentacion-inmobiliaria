from pathlib import Path

from src.utils.download import descargar_archivo


URL = (
    "https://www.ine.es/jaxiT3/files/t/"
    "csv_bdsc/39363.csv"
)

RUTA_SALIDA = Path(
    "data/raw/ine/viviendas_turisticas.csv"
)


def main() -> None:
    descargar_archivo(
        url=URL,
        ruta_salida=RUTA_SALIDA,
    )


if __name__ == "__main__":
    main()