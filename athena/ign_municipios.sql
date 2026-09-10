-- Esquema de la tabla
DESCRIBE ign;

-- Muestra del dataset
SELECT *
FROM ign
LIMIT 10;

-- Filas y municipios distintos
SELECT
    COUNT(*) AS filas,
    COUNT(DISTINCT codigo_ine) AS municipios
FROM ign;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM ign
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(poblacion) AS poblacion_minima,
    MAX(poblacion) AS poblacion_maxima,
    AVG(poblacion) AS poblacion_media,
    approx_percentile(poblacion, 0.5) AS poblacion_mediana,
    MIN(superficie_km2) AS superficie_minima,
    MAX(superficie_km2) AS superficie_maxima,
    AVG(superficie_km2) AS superficie_media,
    approx_percentile(superficie_km2, 0.5) AS superficie_mediana,
    MIN(densidad_poblacion_hab_km2) AS densidad_minima,
    MAX(densidad_poblacion_hab_km2) AS densidad_maxima,
    AVG(densidad_poblacion_hab_km2) AS densidad_media,
    approx_percentile(densidad_poblacion_hab_km2, 0.5) AS densidad_mediana
FROM ign;

-- Valores negativos o coordenadas fuera de rango (imposibles)
SELECT *
FROM ign
WHERE poblacion < 0
   OR superficie_km2 <= 0
   OR densidad_poblacion_hab_km2 < 0
   OR longitud NOT BETWEEN -180 AND 180
   OR latitud NOT BETWEEN -90 AND 90;
