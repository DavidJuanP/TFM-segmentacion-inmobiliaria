import os
from pathlib import Path

import boto3

from src.utils.descargar_archivo import descargar_archivo


URL = (
    "https://cdn.mivau.gob.es/portal-web-mivau/"
    "Datos_MIVAU/CSV/VDP003_01.csv"
)

RAW_BUCKET = os.environ["RAW_BUCKET"]

RUTA_TEMPORAL = Path("/tmp/transacciones.csv")

S3_KEY = "mivau/transacciones.csv"


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
