# TFM-segmentacion-inmobiliaria

## Preparación del entorno

Desde la raíz del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements-dev.txt
```

## Descarga de datos

Las fuentes disponibles están declaradas en `src/config/sources.py`. Para
consultarlas:

```powershell
py -m src.ingestion.download_sources --list
```

Para descargar todas las fuentes:

```powershell
py -m src.ingestion.download_sources
```

También se puede descargar solamente una o varias:

```powershell
py -m src.ingestion.download_sources ine_renta_adrh_31268
py -m src.ingestion.download_sources `
  mivau_alquiler_vdp001_01 `
  sepe_paro_municipios_2025
```

Los archivos existentes se conservan por defecto. Para reemplazarlos:

```powershell
py -m src.ingestion.download_sources --force
```

Las descargas se guardan bajo `data/raw/`, que no se versiona en Git.
