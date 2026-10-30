-- Exposición al evento y recupero de capital de cada crédito con evento 90+.
--
-- La foto no trae el saldo al momento del atraso, así que se estima con el cronograma francés: cuotas
-- puntuales desde el otorgamiento hasta el inicio del atraso, con la tasa y el plazo del crédito. Lo
-- cobrado de capital por encima de lo que tocaba hasta ahí cuenta como recuperado. Las precancelaciones
-- parciales pueden hacer que ese saldo teórico difiera del real: por eso se contrasta con el recupero
-- observado entre fotos (mart_recupero_observado).
with base as (
    select
        *,
        tasa_inicial / 12 as tasa_mes,
        least(greatest(date_diff('month', fecha_otorgamiento, coalesce(fecha_inicio_atraso, fecha_evento_90 - to_days({{ var('dias_evento') }}))), 0), plazo_meses) as cuotas_al_dia
    from {{ ref('int_bondora__prestamos') }}
    where evento_90 and plazo_meses > 0 and monto_otorgado > 0
),
saldo as (
    select
        *,
        case when tasa_mes > 0
             then monto_otorgado * (pow(1 + tasa_mes, plazo_meses) - pow(1 + tasa_mes, cuotas_al_dia)) / (pow(1 + tasa_mes, plazo_meses) - 1)
             else monto_otorgado * (1 - cuotas_al_dia / plazo_meses) end as ead
    from base
)
select
    prestamo_id, pais, rating, cosecha, fecha_otorgamiento, fecha_evento_90, fecha_foto, estado,
    plazo_meses, monto_otorgado, tasa_inicial, cuotas_al_dia, ead,
    least(greatest(capital_pagado - (monto_otorgado - ead), 0), ead) as capital_recuperado,
    date_diff('month', fecha_evento_90, fecha_foto) as meses_desde_evento
from saldo
where ead > 0
