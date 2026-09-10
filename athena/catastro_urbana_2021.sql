-- Esquema de la tabla
DESCRIBE catastro;

-- Muestra del dataset
SELECT * FROM catastro WHERE anio = 2021 LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM catastro WHERE anio = 2021;

-- Municipios y años duplicados
SELECT codigo_ine, municipio, anio, COUNT(*) AS repeticiones
FROM catastro
WHERE anio = 2021
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
    approx_percentile(inmuebles_residenciales, 0.5) AS inmuebles_residenciales_mediana,
    AVG(valor_catastral_total_eur) AS valor_catastral_total_medio,
    AVG(valor_catastral_suelo_eur) AS valor_catastral_suelo_medio,
    approx_percentile(valor_catastral_suelo_eur, 0.5) AS valor_catastral_suelo_mediana,
    AVG(superficie_urbana_m2) AS superficie_urbana_media,
    AVG(parcelas_urbanas) AS parcelas_urbanas_media,
    AVG(valor_catastral_residencial_eur) AS valor_residencial_medio,
    AVG(valor_catastral_suelo_eur_m2) AS valor_suelo_m2_medio,
    approx_percentile(valor_catastral_suelo_eur_m2, 0.5) AS valor_suelo_m2_mediana,
    AVG(valor_catastral_residencial_medio_eur) AS valor_residencial_inmueble_medio,
    approx_percentile(valor_catastral_residencial_medio_eur, 0.5) AS valor_residencial_inmueble_mediana
FROM catastro WHERE anio = 2021;

-- Valores negativos o residenciales mayores que los inmuebles urbanos
SELECT *
FROM catastro
WHERE anio = 2021 and (inmuebles_urbanos < 0
   OR inmuebles_residenciales < 0
   OR inmuebles_residenciales > inmuebles_urbanos
   OR valor_catastral_total_eur < 0
   OR valor_catastral_suelo_eur < 0
   OR superficie_urbana_m2 < 0
   OR parcelas_urbanas < 0
   OR valor_catastral_residencial_eur < 0
   OR valor_catastral_suelo_eur_m2 < 0
   OR valor_catastral_residencial_medio_eur < 0);
