-- Esquema de la tabla
DESCRIBE ine_poblacion;

-- Muestra del dataset
SELECT * FROM ine_poblacion LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM ine_poblacion;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM ine_poblacion
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(poblacion_2025) AS minimo,
    MAX(poblacion_2025) AS maximo,
    AVG(poblacion_2025) AS media,
    approx_percentile(poblacion_2025, 0.5) AS mediana,
    STDDEV(poblacion_2025) AS desviacion_estandar,
    AVG(variacion_poblacion_1_anio) AS variacion_porcentual_media_1_anio,
    AVG(variacion_poblacion_3_anios) AS variacion_porcentual_media_3_anios,
    AVG(variacion_poblacion_5_anios) AS variacion_porcentual_media_5_anios
FROM ine_poblacion;

-- Poblaciones negativas (imposibles)
SELECT *
FROM ine_poblacion
WHERE poblacion_2025 < 0;
