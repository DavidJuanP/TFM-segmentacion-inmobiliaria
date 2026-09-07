-- Esquema de la tabla
DESCRIBE alquiler;

-- Muestra del dataset
SELECT * FROM alquiler LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM alquiler;

-- Registros duplicados en la granularidad del dataset
SELECT
    codigo_ine, municipio, anio, tipo_vivienda, elemento, tipo_medida,
    COUNT(*) AS repeticiones
FROM alquiler
GROUP BY codigo_ine, municipio, anio, tipo_vivienda, elemento, tipo_medida
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(valor) AS minimo,
    MAX(valor) AS maximo,
    MAX(valor) - MIN(valor) AS rango,
    STDDEV(valor) AS desviacion_estandar,
    AVG(valor) AS media,
    approx_percentile(valor, 0.5) AS mediana
FROM alquiler;

-- Valores negativos (imposibles)
SELECT *
FROM alquiler
WHERE valor < 0;
