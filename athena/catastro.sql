-- Esquema de la tabla
DESCRIBE tfm_processed.ine_poblacion;

-- Filas y municipios distintos
SELECT
    COUNT(*) AS filas,
    COUNT(DISTINCT cod_municipio) AS municipios
FROM tfm_processed.ine_poblacion;

-- Municipios duplicados
SELECT
    cod_municipio,
    municipio,
    COUNT(*) AS repeticiones
FROM tfm_processed.ine_poblacion
GROUP BY cod_municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(poblacion) AS minimo,
    MAX(poblacion) AS maximo,
    maximo - minimo AS rango,
    STDDEV(poblacion) AS desviacion_estandar,
    AVG(poblacion) AS media,
    approx_percentile(poblacion, 0.5) AS mediana
FROM tfm_processed.ine_poblacion;

-- Nulos
SELECT
    SUM(CASE WHEN cod_municipio IS NULL THEN 1 ELSE 0 END) AS nulos_codigo,
    SUM(CASE WHEN poblacion IS NULL THEN 1 ELSE 0 END) AS nulos_poblacion
FROM tfm_processed.ine_poblacion;

-- Valores negativos o cero (imposibles)
SELECT *
FROM tfm_processed.ine_poblacion
WHERE poblacion <= 0;