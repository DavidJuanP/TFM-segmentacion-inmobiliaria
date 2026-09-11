-- Esquema de la tabla
DESCRIBE ine_viviendas;

-- Muestra del dataset
SELECT * FROM ine_viviendas LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM ine_viviendas;

-- Municipios duplicados
SELECT codigo_ine, municipio, COUNT(*) AS repeticiones
FROM ine_viviendas
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Principales estadísticos
SELECT
    MIN(viviendas_totales) AS viviendas_minimas,
    MAX(viviendas_totales) AS viviendas_maximas,
    AVG(viviendas_totales) AS viviendas_medias,
    approx_percentile(viviendas_totales, 0.5) AS viviendas_medianas,
    AVG(viviendas_vacias) AS viviendas_vacias_medias,
    AVG(viviendas_uso_esporadico) AS viviendas_esporadicas_medias,
    AVG(porcentaje_viviendas_vacias) AS porcentaje_vacias_medio,
    AVG(porcentaje_viviendas_uso_esporadico) AS porcentaje_esporadicas_medio
FROM ine_viviendas;

-- Valores negativos, porcentajes inválidos o partes mayores que el total
SELECT *
FROM ine_viviendas
WHERE viviendas_totales < 0
   OR viviendas_vacias < 0
   OR viviendas_uso_esporadico < 0
   OR viviendas_vacias + viviendas_uso_esporadico > viviendas_totales
   OR porcentaje_viviendas_vacias NOT BETWEEN 0 AND 100
   OR porcentaje_viviendas_uso_esporadico NOT BETWEEN 0 AND 100;
