CREATE SCHEMA IF NOT EXISTS curated;

CREATE TABLE curated.municipios (
      codigo_ine VARCHAR(5),
      municipio VARCHAR(200),
      provincia VARCHAR(100),
      capital VARCHAR(100),

      poblacion_ign BIGINT,
      superficie_km2 DOUBLE PRECISION,
      densidad_poblacion_hab_km2 DOUBLE PRECISION,
      longitud DOUBLE PRECISION,
      latitud DOUBLE PRECISION,

      codigo_comunidad VARCHAR(2),
      codigo_provincia VARCHAR(2),
      inmuebles_urbanos BIGINT,
      valor_catastral_total_eur DOUBLE PRECISION,
      valor_catastral_suelo_eur DOUBLE PRECISION,
      superficie_urbana_m2 BIGINT,
      parcelas_urbanas BIGINT,
      inmuebles_residenciales BIGINT,
      valor_catastral_residencial_eur DOUBLE PRECISION,
      valor_catastral_suelo_eur_m2 DOUBLE PRECISION,
      valor_catastral_residencial_medio_eur DOUBLE PRECISION,

      edad_media_2025 DOUBLE PRECISION,
      porcentaje_poblacion_menor_18 DOUBLE PRECISION,
      porcentaje_poblacion_65_mas DOUBLE PRECISION,
      diferencia_edad_media_1_anio DOUBLE PRECISION,
      diferencia_edad_media_3_anios DOUBLE PRECISION,

      saldo_total BIGINT,
      saldo_interior BIGINT,
      saldo_exterior BIGINT,

      poblacion_2025 BIGINT,
      variacion_poblacion_1_anio DOUBLE PRECISION,
      variacion_poblacion_3_anios DOUBLE PRECISION,
      variacion_poblacion_5_anios DOUBLE PRECISION,

      renta_neta_media_persona_eur BIGINT,
      renta_neta_media_hogar_eur BIGINT,

      tamanio_medio_hogar DOUBLE PRECISION,

      viviendas_totales BIGINT,
      viviendas_vacias BIGINT,
      viviendas_uso_esporadico BIGINT,
      porcentaje_viviendas_vacias DOUBLE PRECISION,
      porcentaje_viviendas_uso_esporadico DOUBLE PRECISION,

      viviendas_turisticas BIGINT,
      plazas BIGINT,
      plazas_por_vivienda DOUBLE PRECISION,

      total_infracciones BIGINT,

      distancia_costa_km DOUBLE PRECISION,

      alquiler_precio_colectiva_mediana DOUBLE PRECISION,
      alquiler_precio_colectiva_rango_intercuartilico DOUBLE PRECISION,
      alquiler_precio_unifamiliar_mediana DOUBLE PRECISION,
      alquiler_precio_unifamiliar_rango_intercuartilico DOUBLE PRECISION,
      alquiler_superficie_colectiva_mediana DOUBLE PRECISION,
      alquiler_superficie_colectiva_rango_intercuartilico DOUBLE PRECISION,
      alquiler_superficie_unifamiliar_mediana DOUBLE PRECISION,
      alquiler_superficie_unifamiliar_rango_intercuartilico DOUBLE PRECISION,
      alquiler_colectiva_aproximado_eur_m2 DOUBLE PRECISION,
      alquiler_unifamiliar_aproximado_eur_m2 DOUBLE PRECISION,

      variacion_alquiler_precio_colectiva_mediana_1_anio DOUBLE PRECISION,
      variacion_alquiler_precio_unifamiliar_mediana_1_anio DOUBLE PRECISION,
      variacion_alquiler_colectiva_aproximado_eur_m2_1_anio DOUBLE PRECISION,
      variacion_alquiler_unifamiliar_aproximado_eur_m2_1_anio DOUBLE PRECISION,
      diferencia_alquiler_precio_colectiva_rango_intercuartilico_1_anio DOUBLE PRECISION,
      diferencia_alquiler_precio_unifamiliar_rango_intercuartilico_1_anio DOUBLE PRECISION,
      diferencia_alquiler_superficie_colectiva_mediana_1_anio DOUBLE PRECISION,
      diferencia_alquiler_superficie_colectiva_rango_intercuartilico_1_anio DOUBLE PRECISION,
      diferencia_alquiler_superficie_unifamiliar_mediana_1_anio DOUBLE PRECISION,
      diferencia_alquiler_superficie_unifamiliar_rango_intercuartilico_1_anio DOUBLE PRECISION,

      variacion_alquiler_precio_colectiva_mediana_3_anios DOUBLE PRECISION,
      variacion_alquiler_precio_unifamiliar_mediana_3_anios DOUBLE PRECISION,
      variacion_alquiler_colectiva_aproximado_eur_m2_3_anios DOUBLE PRECISION,
      variacion_alquiler_unifamiliar_aproximado_eur_m2_3_anios DOUBLE PRECISION,
      diferencia_alquiler_precio_colectiva_rango_intercuartilico_3_anios DOUBLE PRECISION,
      diferencia_alquiler_precio_unifamiliar_rango_intercuartilico_3_anios DOUBLE PRECISION,
      diferencia_alquiler_superficie_colectiva_mediana_3_anios DOUBLE PRECISION,
      diferencia_alquiler_superficie_colectiva_rango_intercuartilico_3_anios DOUBLE PRECISION,
      diferencia_alquiler_superficie_unifamiliar_mediana_3_anios DOUBLE PRECISION,
      diferencia_alquiler_superficie_unifamiliar_rango_intercuartilico_3_anios DOUBLE PRECISION,

      transacciones_2025 BIGINT,
      transacciones_nuevas_2025 BIGINT,
      transacciones_segunda_mano_2025 BIGINT,

      paro_medio_2025 DOUBLE PRECISION,

      saldo_interior_por_1000_habitantes DOUBLE PRECISION,
      saldo_exterior_por_1000_habitantes DOUBLE PRECISION,
      viviendas_turisticas_por_1000_habitantes DOUBLE PRECISION,
      paro_por_1000_habitantes DOUBLE PRECISION,

      esfuerzo_alquiler_colectiva_pct DOUBLE PRECISION,
      esfuerzo_alquiler_unifamiliar_pct DOUBLE PRECISION,

      porcentaje_superficie_urbana DOUBLE PRECISION,
      diferencia_porcentaje_superficie_urbana_5_anios DOUBLE PRECISION,
      variacion_inmuebles_residenciales_5_anios DOUBLE PRECISION,
      variacion_valor_catastral_residencial_medio_eur_5_anios DOUBLE PRECISION,
      variacion_valor_catastral_suelo_eur_m2_5_anios DOUBLE PRECISION,
      inmuebles_residenciales_por_1000_habitantes DOUBLE PRECISION,
      diferencia_inmuebles_residenciales_5_anios_por_1000_habitantes DOUBLE PRECISION,

      porcentaje_viviendas_turisticas_sobre_inmuebles_residenciales
          DOUBLE PRECISION,

      transacciones_por_1000_inmuebles_residenciales DOUBLE PRECISION,
      transacciones_nuevas_por_1000_inmuebles_residenciales DOUBLE PRECISION,
      transacciones_segunda_mano_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,

      diferencia_transacciones_1_anio_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_3_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_5_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,

      diferencia_transacciones_nuevas_1_anio_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_nuevas_3_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_nuevas_5_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,

      diferencia_transacciones_segunda_mano_1_anio_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_segunda_mano_3_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION,
      diferencia_transacciones_segunda_mano_5_anios_por_1000_inmuebles_residenciales
          DOUBLE PRECISION
  )
  DISTSTYLE AUTO
  SORTKEY (codigo_ine);


SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema = 'curated'
    AND table_name = 'municipios';

-- 21.5 ms elapsed time
COPY curated.municipios
  FROM 's3://s3-tfm-processed-data-159012148774-eu-west-3/integrado/municipios.parquet'
  IAM_ROLE default
  FORMAT AS PARQUET;

SELECT
    COUNT(*) AS filas,
    COUNT(DISTINCT codigo_ine) AS municipios,
    COUNT(*) - COUNT(DISTINCT codigo_ine) AS duplicados
FROM curated.municipios;
