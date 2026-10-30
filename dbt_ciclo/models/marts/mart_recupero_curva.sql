-- Curva de recupero acumulado de capital según los meses desde el evento 90+ (corte transversal de la
-- última foto, con el saldo al evento estimado por cronograma). Mezcla cosechas de distintas edades.
select
    pais,
    least(floor(meses_desde_evento / 6) * 6, 60)    as meses_desde_evento,
    count(*)                                        as creditos,
    sum(ead)                                        as exposicion,
    sum(capital_recuperado)                         as capital_recuperado,
    100.0 * sum(capital_recuperado) / sum(ead)      as recupero_pct
from {{ ref('int_bondora__exposicion') }}
where meses_desde_evento >= 0
group by 1, 2
