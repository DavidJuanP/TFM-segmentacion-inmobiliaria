-- Esquema de la tabla
DESCRIBE transacciones_nuevas;

-- Muestra del dataset
SELECT * FROM transacciones_nuevas LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM transacciones_nuevas;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM transacciones_nuevas
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(transacciones_nuevas_2025) AS minimo,
    MAX(transacciones_nuevas_2025) AS maximo,
    MAX(transacciones_nuevas_2025) - MIN(transacciones_nuevas_2025) AS rango,
    STDDEV(transacciones_nuevas_2025) AS desviacion_estandar,
    AVG(transacciones_nuevas_2025) AS media,
    approx_percentile(transacciones_nuevas_2025, 0.5) AS mediana,
    AVG(variacion_transacciones_nuevas_1_anio) AS variacion_media_1_anio,
    AVG(variacion_transacciones_nuevas_3_anios) AS variacion_media_3_anios,
    AVG(variacion_transacciones_nuevas_5_anios) AS variacion_media_5_anios
FROM transacciones_nuevas;

-- Transacciones negativas (imposibles)
SELECT *
FROM transacciones_nuevas
WHERE transacciones_nuevas_2025 < 0;
