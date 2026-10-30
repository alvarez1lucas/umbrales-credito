-- Aprobación y precio según la deuda-ingreso, valor por valor donde HMDA lo informa exacto (36 a 49).
-- La concentración de otorgados justo debajo de 50 es la huella del límite de política.
select
    producto_corto as producto,
    coalesce(cast(dti_exacto as varchar), dti_tramo, 'sin_dato') as dti,
    coalesce(dti_exacto, case dti_tramo when '<20' then 15 when '20-30' then 25 when '30-36' then 33
                                        when '50-60' then 55 when '>60' then 65 end) as dti_orden,
    count(*)                                       as decisiones,
    count(*) filter (where aprobado)               as aprobadas,
    100.0 * count(*) filter (where aprobado) / count(*) as aprobacion_pct,
    median(spread)                                 as spread_mediano,
    median(tasa)                                   as tasa_mediana
from {{ ref('int_hmda__decisiones') }}
where con_decision
group by 1, 2, 3
