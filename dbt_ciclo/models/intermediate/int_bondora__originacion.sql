-- Créditos con 12 meses de antigüedad y datos de política: carga de la cuota, rating y resultado a 12 meses.
-- Cuota por sistema francés; ingreso mensual declarado.
with base as (
    select
        p.*,
        tasa_inicial / 12 as tasa_mes
    from {{ ref('int_bondora__prestamos') }} p
    where edad_meses >= 12 and rating is not null and ingreso > 0 and plazo_meses > 0 and tasa_inicial > 0
)
select
    prestamo_id, pais, rating, fecha_otorgamiento, monto_otorgado, tasa_inicial, plazo_meses, ingreso,
    monto_otorgado * tasa_mes / (1 - pow(1 + tasa_mes, -plazo_meses))           as cuota,
    100.0 * monto_otorgado * tasa_mes / (1 - pow(1 + tasa_mes, -plazo_meses)) / ingreso as carga_pct,
    coalesce(evento_90 and date_diff('month', fecha_otorgamiento, fecha_evento_90) <= 12, false) as evento_12m
from base
