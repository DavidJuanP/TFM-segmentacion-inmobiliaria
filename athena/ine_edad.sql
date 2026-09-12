-- Esquema de la tabla
DESCRIBE ine_edad;

-- Muestra del dataset
SELECT * FROM ine_edad LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM ine_edad;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM ine_edad
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(edad_media_2025) AS minimo,
    MAX(edad_media_2025) AS maximo,
    MAX(edad_media_2025) - MIN(edad_media_2025) AS rango,
    STDDEV(edad_media_2025) AS desviacion_estandar,
    AVG(edad_media_2025) AS media,
    approx_percentile(edad_media_2025, 0.5) AS mediana,
    MIN(diferencia_edad_media_1_anio) AS diferencia_1_anio_minima,
    MAX(diferencia_edad_media_1_anio) AS diferencia_1_anio_maxima,
    AVG(diferencia_edad_media_1_anio) AS diferencia_1_anio_media,
    MIN(diferencia_edad_media_3_anios) AS diferencia_3_anios_minima,
    MAX(diferencia_edad_media_3_anios) AS diferencia_3_anios_maxima,
    AVG(diferencia_edad_media_3_anios) AS diferencia_3_anios_media
FROM ine_edad;

-- Edades fuera del rango posible
SELECT *
FROM ine_edad
WHERE edad_media_2025 NOT BETWEEN 0 AND 100
   OR ABS(diferencia_edad_media_1_anio) > 100
   OR ABS(diferencia_edad_media_3_anios) > 100;
