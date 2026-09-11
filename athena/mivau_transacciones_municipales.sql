-- Esquema de la tabla
DESCRIBE mivau_transacciones_municipales;

-- Muestra del dataset
SELECT * FROM mivau_transacciones_municipales LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM mivau_transacciones_municipales;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM mivau_transacciones_municipales
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(transacciones_2025) AS minimo,
    MAX(transacciones_2025) AS maximo,
    MAX(transacciones_2025) - MIN(transacciones_2025) AS rango,
    STDDEV(transacciones_2025) AS desviacion_estandar,
    AVG(transacciones_2025) AS media,
    approx_percentile(transacciones_2025, 0.5) AS mediana,
    AVG(variacion_transacciones_1_anio) AS variacion_media_1_anio,
    AVG(variacion_transacciones_3_anios) AS variacion_media_3_anios,
    AVG(variacion_transacciones_5_anios) AS variacion_media_5_anios
FROM mivau_transacciones_municipales;

-- Transacciones negativas (imposibles)
SELECT *
FROM mivau_transacciones_municipales
WHERE transacciones_2025 < 0;
