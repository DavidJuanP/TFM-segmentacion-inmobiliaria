import os
from pathlib import Path

import boto3

from src.utils.descargar_archivo import descargar_archivo


URL = (
    "https://www.ign.es/resources/ane/"
    "Informacion_Geografica_Destacada/"
    "IGN_INFOGEO_MUNICIPIOS.xlsx"
)

RAW_BUCKET = os.environ["RAW_BUCKET"]

RUTA_TEMPORAL = Path("/tmp/municipios.xlsx")

S3_KEY = "ign/municipios.xlsx"


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