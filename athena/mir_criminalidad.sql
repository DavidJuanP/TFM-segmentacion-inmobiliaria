-- Esquema de la tabla
DESCRIBE criminalidad;

-- Muestra del dataset
SELECT * FROM criminalidad LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM criminalidad;

-- Municipios duplicados
SELECT codigo_ine, municipio, anio, COUNT(*) AS repeticiones
FROM criminalidad
GROUP BY codigo_ine, municipio, anio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(total_infracciones) AS minimo,
    MAX(total_infracciones) AS maximo,
    MAX(total_infracciones) - MIN(total_infracciones) AS rango,
    STDDEV(total_infracciones) AS desviacion_estandar,
    AVG(total_infracciones) AS media,
    approx_percentile(total_infracciones, 0.5) AS mediana
FROM criminalidad;

-- Valores negativos o años distintos del procesado
SELECT *
FROM criminalidad
WHERE total_infracciones < 0 OR anio <> 2025;
