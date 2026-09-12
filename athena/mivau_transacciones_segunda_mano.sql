-- Esquema de la tabla
DESCRIBE mivau_transacciones_segunda_mano;

-- Muestra del dataset
SELECT * FROM mivau_transacciones_segunda_mano LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM mivau_transacciones_segunda_mano;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM mivau_transacciones_segunda_mano
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(transacciones_segunda_mano_2025) AS minimo,
    MAX(transacciones_segunda_mano_2025) AS maximo,
    MAX(transacciones_segunda_mano_2025) - MIN(transacciones_segunda_mano_2025) AS rango,
    STDDEV(transacciones_segunda_mano_2025) AS desviacion_estandar,
    AVG(transacciones_segunda_mano_2025) AS media,
    approx_percentile(transacciones_segunda_mano_2025, 0.5) AS mediana,
    AVG(diferencia_transacciones_segunda_mano_1_anio) AS diferencia_media_1_anio,
    AVG(diferencia_transacciones_segunda_mano_3_anios) AS diferencia_media_3_anios,
    AVG(diferencia_transacciones_segunda_mano_5_anios) AS diferencia_media_5_anios
FROM mivau_transacciones_segunda_mano;

-- Transacciones negativas (imposibles)
SELECT *
FROM mivau_transacciones_segunda_mano
WHERE transacciones_segunda_mano_2025 < 0;
