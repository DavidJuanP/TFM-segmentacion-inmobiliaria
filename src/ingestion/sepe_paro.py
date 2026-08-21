from pathlib import Path

from src.utils.download import descargar_archivo


URL = (
    "https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/Paro_por_municipios_2025_csv.csv"
)

RUTA_SALIDA = Path(
    "data/raw/sepe/paro.csv"
)


def main() -> None:
    descargar_archivo(
        url=URL,
        ruta_salida=RUTA_SALIDA,
    )


if __name__ == "__main__":
    main()