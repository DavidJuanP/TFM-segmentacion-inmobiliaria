import os
from pathlib import Path

import boto3

from src.utils.descargar_archivo import descargar_archivo


URL = (
    "https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/Paro_por_municipios_2025_csv.csv"
)

RAW_BUCKET = os.environ["RAW_BUCKET"]

RUTA_TEMPORAL = Path("/tmp/paro.csv")

S3_KEY = "sepe/paro.csv"


def main() -> None:
    descargar_archivo(
        url=URL,
        ruta_salida=RUTA_TEMPORAL,
    )

    s3 = boto3.client("s3")

    s3.upload_file(
        str(RUTA_TEMPORAL),
        RAW_BUCKET,
        S3_KEY,
    )

    print(
        f"Archivo subido a "
        f"s3://{RAW_BUCKET}/{S3_KEY}"
    )


if __name__ == "__main__":
    main()
