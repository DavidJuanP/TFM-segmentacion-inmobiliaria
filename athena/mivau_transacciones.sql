-- Esquema de la tabla
DESCRIBE transacciones;

-- Muestra del dataset
SELECT * FROM transacciones LIMIT 10;

-- Filas y provincias distintas
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_provincia) AS provincias
FROM transacciones;

-- Registros duplicados en la granularidad del dataset
SELECT codigo_provincia, provincia, anio, trimestre, tipo_vivienda,
       COUNT(*) AS repeticiones
FROM transacciones
GROUP BY codigo_provincia, provincia, anio, trimestre, tipo_vivienda
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(numero_transacciones) AS transacciones_minimas,
    MAX(numero_transacciones) AS transacciones_maximas,
    AVG(numero_transacciones) AS transacciones_medias,
    approx_percentile(numero_transacciones, 0.5) AS transacciones_medianas,
    STDDEV(numero_transacciones) AS transacciones_desviacion,
    MIN(valor_transacciones_eur) AS valor_minimo,
    MAX(valor_transacciones_eur) AS valor_maximo,
    AVG(valor_transacciones_eur) AS valor_medio,
    approx_percentile(valor_transacciones_eur, 0.5) AS valor_mediano
FROM transacciones;

-- Valores negativos o trimestres fuera de rango
SELECT *
FROM transacciones
WHERE numero_transacciones < 0
   OR valor_transacciones_eur < 0
   OR trimestre NOT BETWEEN 1 AND 4;
