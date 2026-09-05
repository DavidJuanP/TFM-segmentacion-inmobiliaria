import os
from pathlib import Path

import boto3

from src.utils.descargar_archivo import descargar_archivo


URL = (
    "https://apps.fomento.gob.es/BoletinOnline2/sedal/34010240.XLS"
)

RAW_BUCKET = os.environ["RAW_BUCKET"]

RUTA_TEMPORAL = Path("/tmp/transacciones_nuevas.xls")

S3_KEY = "mivau/transacciones_nuevas.xls"


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
