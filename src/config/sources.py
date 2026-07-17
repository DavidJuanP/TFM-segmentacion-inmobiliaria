SOURCES = {
    "mivau_alquiler_vdp001_01": {
        "source": "MIVAU",
        "description": "Referencia del Precio del Alquiler de Vivienda por municipios y años",
        "url": "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv",
        "format": "csv",
        "raw_path": "data/raw/mivau/alquiler_vdp001_01.csv",
    },

    "mivau_parque_viviendas_vdp002_01": {
        "source": "MIVAU",
        "description": "Estimación del parque de viviendas por localidad y año",
        "url": "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP002_01.csv",
        "format": "csv",
        "raw_path": "data/raw/mivau/parque_viviendas_vdp002_01.csv",
    },

    "ine_renta_adrh_31268": {
        "source": "INE",
        "description": "Indicadores de renta media y mediana. Atlas de Distribución de Renta de los Hogares",
        "url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/31268.csv",
        "url_json": "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/31268?tip=AM",
        "format": "csv",
        "raw_path": "data/raw/ine/renta_adrh_31268.csv",
    },

    "ine_poblacion_edad_33799": {
        "source": "INE",
        "description": "Población por sexo, municipios y edad año a año",
        "url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/33799.csv",
        "url_json": "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/33799?tip=AM",
        "format": "csv",
        "raw_path": "data/raw/ine/poblacion_edad_33799.csv",
    },

    "ine_poblacion_nacionalidad_33957": {
        "source": "INE",
        "description": "Población por sexo, municipios, nacionalidad español/extranjero y edad en grandes grupos",
        "url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/33957.csv",
        "url_json": "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/33957?tip=AM",
        "format": "csv",
        "raw_path": "data/raw/ine/poblacion_nacionalidad_33957.csv",
    },

    "ine_viviendas_turisticas_39363": {
        "source": "INE",
        "description": "Viviendas turísticas, plazas y plazas por vivienda turística por municipios",
        "url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/39363.csv",
        "url_json": "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/39363?tip=AM",
        "format": "csv",
        "raw_path": "data/raw/ine/viviendas_turisticas_39363.csv",
    },

    "ine_viviendas_intensidad_uso_59531": {
        "source": "INE",
        "description": "Viviendas según intensidad de uso. Censo de Población y Viviendas 2021",
        "url": "https://www.ine.es/jaxi/files/tpx/csv_bdsc/59531.csv",
        "url_json": "https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/59531?tip=AM",
        "format": "csv",
        "raw_path": "data/raw/ine/viviendas_intensidad_uso_59531.csv",
    },

    "sepe_paro_municipios_2025": {
        "source": "SEPE",
        "description": "Paro registrado por municipios. Año 2025",
        "url": "https://sede.sepe.gob.es/es/portaltrabaja/resources/sede/datos_abiertos/datos/Paro_por_municipios_2025_csv.csv",
        "format": "csv",
        "raw_path": "data/raw/sepe/paro_municipios_2025.csv",
    },

    "cnig_limites_municipales": {
        "source": "CNIG/IGN",
        "description": "Límites municipales, provinciales y autonómicos",
        "url": "https://api-features.ign.es/collections/administrativeunit",
        "format": "api_features",
        "raw_path": "data/raw/cnig/limites_municipales/",
    },
}