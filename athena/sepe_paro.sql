-- Esquema de la tabla
DESCRIBE sepe;

-- Muestra del dataset
SELECT
    *
FROM sepe
LIMIT 10;

-- Filas y municipios distintos
SELECT
    COUNT(*) AS filas,
    COUNT(DISTINCT codigo_ine) AS municipios
FROM sepe;

-- Municipios duplicados
SELECT
    codigo_ine,
    municipio,
    COUNT(*) AS repeticiones
FROM sepe
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 12
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(paro_medio_2025) AS minimo,
    MAX(paro_medio_2025) AS maximo,
    MAX(paro_medio_2025) - MIN(paro_medio_2025) AS rango,
    STDDEV(paro_medio_2025) AS desviacion_estandar,
    AVG(paro_medio_2025) AS media,
    approx_percentile(paro_medio_2025, 0.5) AS mediana
FROM sepe;

-- Valores nulos
SELECT
    SUM(CASE WHEN codigo_ine IS NULL THEN 1 ELSE 0 END) AS nulos_codigo,
    SUM(CASE WHEN paro_medio_2025 IS NULL THEN 1 ELSE 0 END) AS nulos_paro
FROM sepe;

-- Valores negativos(imposibles)
SELECT *
FROM sepe
WHERE paro_medio_2025 < 0;