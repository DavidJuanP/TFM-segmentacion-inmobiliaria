# SUCIO

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

## Procesamiento

Cada fuente en crudo dispone de un módulo de limpieza. Todos normalizan los
tipos, validan su clave natural y escriben un Parquet con compresión Zstandard
bajo `data/processed/`:

```powershell
py -m src.processing.ine_poblacion
py -m src.processing.ign_municipios
py -m src.processing.ine_edad
py -m src.processing.ine_migracion
py -m src.processing.ine_renta
py -m src.processing.ine_superficie
py -m src.processing.ine_tamanio_hogar
py -m src.processing.ine_viviendas_turisticas
py -m src.processing.mivau_alquiler
py -m src.processing.mivau_transacciones
py -m src.processing.sepe_paro
```

Los datos ausentes se conservan como nulos; no se imputan durante la limpieza.
En el fichero del SEPE, el valor protegido `<5` también se representa como
nulo, acompañado de una columna booleana `*_censurado` para no perder esa
información. La fuente de transacciones tiene granularidad provincial y la de
superficie no incluye código INE, particularidades que se mantienen en sus
resultados.
