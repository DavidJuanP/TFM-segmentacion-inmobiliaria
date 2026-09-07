-- Esquema de la tabla
DESCRIBE renta;

-- Muestra del dataset
SELECT * FROM renta LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM renta;

-- Municipios y años duplicados
SELECT codigo_ine, municipio, anio, COUNT(*) AS repeticiones
FROM renta
GROUP BY codigo_ine, municipio, anio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(renta_neta_media_persona_eur) AS renta_persona_minima,
    MAX(renta_neta_media_persona_eur) AS renta_persona_maxima,
    AVG(renta_neta_media_persona_eur) AS renta_persona_media,
    approx_percentile(renta_neta_media_persona_eur, 0.5) AS renta_persona_mediana,
    MIN(renta_mediana_unidad_consumo_eur) AS renta_uc_minima,
    MAX(renta_mediana_unidad_consumo_eur) AS renta_uc_maxima,
    AVG(renta_mediana_unidad_consumo_eur) AS renta_uc_media,
    MIN(renta_neta_media_hogar_eur) AS renta_hogar_minima,
    MAX(renta_neta_media_hogar_eur) AS renta_hogar_maxima,
    AVG(renta_neta_media_hogar_eur) AS renta_hogar_media
FROM renta;

-- Rentas negativas (imposibles)
SELECT *
FROM renta
WHERE renta_neta_media_persona_eur < 0
   OR renta_mediana_unidad_consumo_eur < 0
   OR renta_neta_media_hogar_eur < 0;
