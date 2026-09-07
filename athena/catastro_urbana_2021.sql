-- Esquema de la tabla
DESCRIBE urbana_2021;

-- Muestra del dataset
SELECT * FROM urbana_2021 LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM urbana_2021;

-- Municipios y años duplicados
SELECT codigo_ine, municipio, anio, COUNT(*) AS repeticiones
FROM urbana_2021
GROUP BY codigo_ine, municipio, anio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(inmuebles_urbanos) AS inmuebles_urbanos_minimo,
    MAX(inmuebles_urbanos) AS inmuebles_urbanos_maximo,
    AVG(inmuebles_urbanos) AS inmuebles_urbanos_medio,
    approx_percentile(inmuebles_urbanos, 0.5) AS inmuebles_urbanos_mediana,
    AVG(inmuebles_residenciales) AS inmuebles_residenciales_medio,
    AVG(valor_catastral_total_eur) AS valor_catastral_total_medio,
    AVG(valor_catastral_suelo_eur) AS valor_catastral_suelo_medio,
    AVG(superficie_urbana_m2) AS superficie_urbana_media,
    AVG(parcelas_urbanas) AS parcelas_urbanas_media,
    AVG(valor_catastral_residencial_eur) AS valor_residencial_medio,
    AVG(valor_catastral_suelo_eur_m2) AS valor_suelo_m2_medio,
    AVG(valor_catastral_residencial_medio_eur) AS valor_residencial_inmueble_medio
FROM urbana_2021;

-- Valores negativos o residenciales mayores que los inmuebles urbanos
SELECT *
FROM urbana_2021
WHERE inmuebles_urbanos < 0
   OR inmuebles_residenciales < 0
   OR inmuebles_residenciales > inmuebles_urbanos
   OR valor_catastral_total_eur < 0
   OR valor_catastral_suelo_eur < 0
   OR superficie_urbana_m2 < 0
   OR parcelas_urbanas < 0
   OR valor_catastral_residencial_eur < 0
   OR valor_catastral_suelo_eur_m2 < 0
   OR valor_catastral_residencial_medio_eur < 0;
