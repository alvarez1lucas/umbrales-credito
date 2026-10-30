-- Pérdida dado el evento (LGD) por país: 1 - recupero de capital de los eventos con 36 meses o más de
-- maduración, ponderado por exposición.
select
    pais,
    count(*)                                           as creditos,
    sum(ead)                                           as exposicion,
    100.0 * sum(capital_recuperado) / sum(ead)         as recupero_pct,
    100.0 - 100.0 * sum(capital_recuperado) / sum(ead) as lgd_pct
from {{ ref('int_bondora__exposicion') }}
where meses_desde_evento >= 36
group by 1
having count(*) >= 200
