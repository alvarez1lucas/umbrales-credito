-- Resultados por grupo demográfico: rechazo, perfil de riesgo y precio. Son diferencias brutas;
-- la brecha condicional y el índice de impacto adverso están en ciclo.originacion.
select
    grupo,
    count(*)                                                 as decisiones,
    100.0 * count(*) filter (where aprobado) / count(*)      as aprobacion_pct,
    100.0 * count(*) filter (where resultado = 'rechazado') / count(*) as rechazo_pct,
    median(ingreso_miles)                                    as ingreso_mediano_miles,
    median(monto)                                            as monto_mediano,
    median(ltv)                                              as ltv_mediano,
    median(dti_exacto)                                       as dti_mediano_36_49,
    100.0 * count(*) filter (where dti_tramo in ('50-60', '>60')) / count(*) as dti_50_o_mas_pct,
    median(spread) filter (where resultado = 'otorgado')     as spread_mediano
from {{ ref('int_hmda__decisiones') }}
where con_decision
group by 1
