-- Esquema de la tabla
DESCRIBE edad_parquet;

-- Muestra del dataset
SELECT * FROM edad_parquet LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM edad_parquet;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM edad_parquet
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(edad_media_2022) AS minimo,
    MAX(edad_media_2022) AS maximo,
    MAX(edad_media_2022) - MIN(edad_media_2022) AS rango,
    STDDEV(edad_media_2022) AS desviacion_estandar,
    AVG(edad_media_2022) AS media,
    approx_percentile(edad_media_2022, 0.5) AS mediana,
    MIN(variacion_edad_media_5_anios) AS variacion_minima,
    MAX(variacion_edad_media_5_anios) AS variacion_maxima,
    AVG(variacion_edad_media_5_anios) AS variacion_media
FROM edad_parquet;

-- Edades fuera del rango posible
SELECT *
FROM edad_parquet
WHERE edad_media_2022 NOT BETWEEN 0 AND 100
   OR ABS(variacion_edad_media_5_anios) > 100;
