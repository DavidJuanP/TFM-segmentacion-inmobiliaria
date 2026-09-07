-- Esquema de la tabla
DESCRIBE tamanio_hogar;

-- Muestra del dataset
SELECT * FROM tamanio_hogar LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM tamanio_hogar;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM tamanio_hogar
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(tamanio_medio_hogar) AS minimo,
    MAX(tamanio_medio_hogar) AS maximo,
    MAX(tamanio_medio_hogar) - MIN(tamanio_medio_hogar) AS rango,
    STDDEV(tamanio_medio_hogar) AS desviacion_estandar,
    AVG(tamanio_medio_hogar) AS media,
    approx_percentile(tamanio_medio_hogar, 0.5) AS mediana
FROM tamanio_hogar;

-- Tamaños medios fuera del rango aproximado posible
SELECT *
FROM tamanio_hogar
WHERE tamanio_medio_hogar < 1 OR tamanio_medio_hogar > 5;
