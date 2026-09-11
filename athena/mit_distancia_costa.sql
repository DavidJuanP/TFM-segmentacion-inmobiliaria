-- Esquema de la tabla
DESCRIBE mit;

-- Muestra del dataset
SELECT * FROM mit LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM mit;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM mit
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(distancia_costa_km) AS minimo,
    MAX(distancia_costa_km) AS maximo,
    MAX(distancia_costa_km) - MIN(distancia_costa_km) AS rango,
    STDDEV(distancia_costa_km) AS desviacion_estandar,
    AVG(distancia_costa_km) AS media,
    approx_percentile(distancia_costa_km, 0.5) AS mediana
FROM mit;

-- Distancias negativas (imposibles)
SELECT *
FROM mit
WHERE distancia_costa_km < 0;
