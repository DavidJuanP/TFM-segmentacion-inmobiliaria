from pathlib import Path

from src.utils.download import descargar_archivo


URL = (
    "https://www.ign.es/resources/ane/"
    "Informacion_Geografica_Destacada/"
    "IGN_INFOGEO_MUNICIPIOS.xlsx"
)

RUTA_SALIDA = Path(
    "data/raw/ign/municipios/IGN_INFOGEO_MUNICIPIOS.xlsx"
)


def main() -> None:
    descargar_archivo(
        url=URL,
        ruta_salida=RUTA_SALIDA,
    )


if __name__ == "__main__":
    main()