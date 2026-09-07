-- Esquema de la tabla
DESCRIBE poblacion;

-- Muestra del dataset
SELECT * FROM poblacion LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM poblacion;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM poblacion
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
    AVG(variacion_poblacion_1_anio) AS variacion_media_1_anio,
    AVG(variacion_poblacion_3_anios) AS variacion_media_3_anios,
    AVG(variacion_poblacion_5_anios) AS variacion_media_5_anios
FROM poblacion;

-- Poblaciones negativas (imposibles)
SELECT *
FROM poblacion
WHERE poblacion_2025 < 0;
