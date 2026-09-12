-- Esquema de la tabla
DESCRIBE integrado;

-- Muestra del dataset
SELECT *
FROM integrado
LIMIT 10;

-- Filas y municipios distintos: ambos valores deben coincidir
SELECT
    COUNT(*) AS filas,
    COUNT(DISTINCT codigo_ine) AS municipios,
    COUNT(*) - COUNT(DISTINCT codigo_ine) AS filas_adicionales
FROM integrado;

-- Identificadores incompletos
SELECT *
FROM integrado
WHERE codigo_ine IS NULL
   OR municipio IS NULL
   OR provincia IS NULL;

-- Municipios duplicados
SELECT
    codigo_ine,
    municipio,
    COUNT(*) AS repeticiones
FROM integrado
GROUP BY codigo_ine, municipio
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Periodos incorporados al dataset integrado
SELECT
    anio_catastro,
    anio_catastro_2021,
    anio_renta,
    anio_migracion,
    anio_criminalidad,
    periodo_viviendas_turisticas,
    COUNT(*) AS municipios
FROM integrado
GROUP BY
    anio_catastro,
    anio_catastro_2021,
    anio_renta,
    anio_migracion,
    anio_criminalidad,
    periodo_viviendas_turisticas
ORDER BY municipios DESC;

-- Cobertura y valores nulos de las principales fuentes
SELECT
    COUNT(*) AS municipios_totales,
    COUNT(*) - COUNT(poblacion_2025) AS nulos_poblacion,
    COUNT(*) - COUNT(edad_media_2025) AS nulos_edad,
    COUNT(*) - COUNT(renta_neta_media_persona_eur) AS nulos_renta,
    COUNT(*) - COUNT(tamanio_medio_hogar) AS nulos_tamanio_hogar,
    COUNT(*) - COUNT(saldo_interior) AS nulos_migracion,
    COUNT(*) - COUNT(viviendas_totales) AS nulos_viviendas,
    COUNT(*) - COUNT(viviendas_turisticas) AS nulos_viviendas_turisticas,
    COUNT(*) - COUNT(total_infracciones) AS nulos_criminalidad,
    COUNT(*) - COUNT(distancia_costa_km) AS nulos_distancia_costa,
    COUNT(*) - COUNT(transacciones_2025) AS nulos_transacciones,
    COUNT(*) - COUNT(paro_medio_2025) AS nulos_paro,
    COUNT(*) - COUNT(inmuebles_residenciales) AS nulos_catastro_2026,
    COUNT(*) - COUNT(inmuebles_residenciales_catastro_2021)
        AS nulos_catastro_2021
FROM integrado;

-- Principales estadísticos de variables municipales y calculadas
SELECT
    AVG(poblacion_2025) AS poblacion_media,
    approx_percentile(poblacion_2025, 0.5) AS poblacion_mediana,
    AVG(edad_media_2025) AS edad_media,
    AVG(renta_neta_media_persona_eur) AS renta_persona_media,
    approx_percentile(renta_neta_media_persona_eur, 0.5)
        AS renta_persona_mediana,
    AVG(tamanio_medio_hogar) AS tamanio_hogar_medio,
    AVG(viviendas_turisticas_por_1000_habitantes)
        AS viviendas_turisticas_por_1000_media,
    AVG(paro_por_1000_habitantes) AS paro_por_1000_media,
    AVG(porcentaje_superficie_urbana) AS superficie_urbana_porcentaje_medio,
    AVG(inmuebles_residenciales_por_1000_habitantes)
        AS inmuebles_residenciales_por_1000_media,
    AVG(valor_catastral_suelo_eur_m2) AS valor_suelo_m2_medio,
    AVG(valor_catastral_residencial_medio_eur)
        AS valor_residencial_medio,
    AVG(transacciones_2025) AS transacciones_media,
    approx_percentile(transacciones_2025, 0.5) AS transacciones_mediana,
    AVG(distancia_costa_km) AS distancia_costa_media
FROM integrado;

-- Resumen de las variaciones temporales empleadas en el modelo
SELECT
    AVG(variacion_poblacion_1_anio) AS variacion_poblacion_1_media,
    AVG(variacion_poblacion_3_anios) AS variacion_poblacion_3_media,
    AVG(variacion_poblacion_5_anios) AS variacion_poblacion_5_media,
    AVG(variacion_edad_media_1_anio) AS variacion_edad_1_media,
    AVG(variacion_edad_media_3_anios) AS variacion_edad_3_media,
    AVG(variacion_transacciones_1_anio) AS variacion_transacciones_1_media,
    AVG(variacion_transacciones_3_anios) AS variacion_transacciones_3_media,
    AVG(variacion_transacciones_5_anios) AS variacion_transacciones_5_media,
    AVG(variacion_inmuebles_residenciales_5_anios)
        AS variacion_inmuebles_residenciales_media,
    AVG(variacion_valor_catastral_residencial_medio_eur_5_anios)
        AS variacion_valor_residencial_medio_media,
    AVG(variacion_superficie_urbana_m2_5_anios)
        AS variacion_superficie_urbana_media,
    AVG(variacion_valor_catastral_suelo_eur_m2_5_anios)
        AS variacion_valor_suelo_m2_media
FROM integrado;

-- Valores imposibles o incoherentes que requieren revisión
SELECT *
FROM integrado
WHERE poblacion_2025 <= 0
   OR superficie_km2 <= 0
   OR viviendas_totales < 0
   OR viviendas_vacias < 0
   OR viviendas_vacias > viviendas_totales
   OR viviendas_uso_esporadico < 0
   OR viviendas_uso_esporadico > viviendas_totales
   OR total_infracciones < 0
   OR paro_medio_2025 < 0
   OR transacciones_2025 < 0
   OR inmuebles_residenciales < 0
   OR porcentaje_superficie_urbana < 0
   OR distancia_costa_km < 0;

-- Municipios con más valores ausentes entre las variables principales
SELECT
    codigo_ine,
    municipio,
    provincia,
    IF(poblacion_2025 IS NULL, 1, 0)
      + IF(edad_media_2025 IS NULL, 1, 0)
      + IF(renta_neta_media_persona_eur IS NULL, 1, 0)
      + IF(tamanio_medio_hogar IS NULL, 1, 0)
      + IF(saldo_interior IS NULL, 1, 0)
      + IF(viviendas_totales IS NULL, 1, 0)
      + IF(viviendas_turisticas IS NULL, 1, 0)
      + IF(total_infracciones IS NULL, 1, 0)
      + IF(distancia_costa_km IS NULL, 1, 0)
      + IF(transacciones_2025 IS NULL, 1, 0)
      + IF(paro_medio_2025 IS NULL, 1, 0)
      + IF(inmuebles_residenciales IS NULL, 1, 0)
        AS variables_ausentes
FROM integrado
ORDER BY variables_ausentes DESC, codigo_ine
LIMIT 100;
