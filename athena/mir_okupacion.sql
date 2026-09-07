-- Esquema de la tabla
DESCRIBE okupacion;

-- Muestra del dataset
SELECT * FROM okupacion LIMIT 10;

-- Filas y comunidades distintas
SELECT COUNT(*) AS filas, COUNT(DISTINCT comunidad) AS comunidades
FROM okupacion;

-- Comunidades y años duplicados
SELECT comunidad, anio, COUNT(*) AS repeticiones
FROM okupacion
GROUP BY comunidad, anio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(total_okupaciones) AS minimo,
    MAX(total_okupaciones) AS maximo,
    MAX(total_okupaciones) - MIN(total_okupaciones) AS rango,
    STDDEV(total_okupaciones) AS desviacion_estandar,
    AVG(total_okupaciones) AS media,
    approx_percentile(total_okupaciones, 0.5) AS mediana
FROM okupacion;

-- Valores negativos (imposibles)
SELECT *
FROM okupacion
WHERE total_okupaciones < 0;
