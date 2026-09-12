-- Esquema de la tabla
DESCRIBE mivau_alquiler;

-- Muestra del dataset
SELECT * FROM mivau_alquiler LIMIT 10;

-- Filas y municipios distintos
SELECT COUNT(*) AS filas, COUNT(DISTINCT codigo_ine) AS municipios
FROM mivau_alquiler;

-- Registros duplicados en la granularidad del dataset
SELECT
    codigo_ine, municipio, anio, tipo_vivienda, elemento, tipo_medida,
    COUNT(*) AS repeticiones
FROM mivau_alquiler
GROUP BY codigo_ine, municipio, anio, tipo_vivienda, elemento, tipo_medida
HAVING COUNT(*) > 1
ORDER BY repeticiones DESC;

-- Medidas generadas: solo deben aparecer MEDIANA y RANGO_INTERCUARTILICO
SELECT
    elemento,
    tipo_vivienda,
    tipo_medida,
    COUNT(*) AS registros,
    COUNT(valor) AS valores_disponibles
FROM mivau_alquiler
GROUP BY elemento, tipo_vivienda, tipo_medida
ORDER BY elemento, tipo_vivienda, tipo_medida;

-- Valores negativos (imposibles)
SELECT *
FROM mivau_alquiler
WHERE valor < 0;
