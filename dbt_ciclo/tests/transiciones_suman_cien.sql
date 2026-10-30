-- Las filas de cada tramo de origen suman 100% en cada par de fotos.
select fecha_desde, fecha_hasta, tramo_desde, sum(pct_del_tramo) as total
from {{ ref('mart_roll_rates') }}
group by 1, 2, 3
having abs(sum(pct_del_tramo) - 100) > 0.001
