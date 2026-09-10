-- Esquema de la tabla
DESCRIBE viviendas_turisticas_parquet;

-- Muestra del dataset
SELECT * FROM viviendas_turisticas_parquet LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM viviendas_turisticas_parquet;

-- Municipios y periodos duplicados
SELECT codigo_ine, municipio, periodo, COUNT(*) AS repeticiones
FROM viviendas_turisticas_parquet
GROUP BY codigo_ine, municipio, periodo
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(viviendas_turisticas) AS viviendas_minimas,
    MAX(viviendas_turisticas) AS viviendas_maximas,
    AVG(viviendas_turisticas) AS viviendas_medias,
    approx_percentile(viviendas_turisticas, 0.5) AS viviendas_medianas,
    MIN(plazas) AS plazas_minimas,
    MAX(plazas) AS plazas_maximas,
    AVG(plazas) AS plazas_medias,
    AVG(plazas_por_vivienda) AS plazas_por_vivienda_media
FROM viviendas_turisticas_parquet;

-- Valores negativos o periodos incoherentes
SELECT *
FROM viviendas_turisticas_parquet
WHERE viviendas_turisticas < 0
   OR plazas < 0
   OR plazas_por_vivienda < 0
   OR mes NOT BETWEEN 1 AND 12
   OR periodo <> CONCAT(CAST(anio AS VARCHAR), 'M', LPAD(CAST(mes AS VARCHAR), 2, '0'));
