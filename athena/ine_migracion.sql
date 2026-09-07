-- Esquema de la tabla
DESCRIBE migracion;

-- Muestra del dataset
SELECT * FROM migracion LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM migracion;

-- Municipios duplicados
SELECT codigo_ine, municipio, anio, COUNT(*) AS repeticiones
FROM migracion
GROUP BY codigo_ine, municipio, anio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(saldo_total) AS saldo_total_minimo,
    MAX(saldo_total) AS saldo_total_maximo,
    AVG(saldo_total) AS saldo_total_medio,
    approx_percentile(saldo_total, 0.5) AS saldo_total_mediano,
    STDDEV(saldo_total) AS saldo_total_desviacion,
    MIN(saldo_interior) AS saldo_interior_minimo,
    MAX(saldo_interior) AS saldo_interior_maximo,
    AVG(saldo_interior) AS saldo_interior_medio,
    MIN(saldo_exterior) AS saldo_exterior_minimo,
    MAX(saldo_exterior) AS saldo_exterior_maximo,
    AVG(saldo_exterior) AS saldo_exterior_medio
FROM migracion;

-- Años distintos del periodo procesado
SELECT *
FROM migracion
WHERE anio <> 2024;
