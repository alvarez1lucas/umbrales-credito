-- Mora a 12 meses según la carga de la cuota sobre el ingreso, por tramo.
select
    case when carga_pct < 5 then '<5' when carga_pct < 10 then '5-10' when carga_pct < 15 then '10-15'
         when carga_pct < 20 then '15-20' when carga_pct < 30 then '20-30' when carga_pct < 40 then '30-40'
         else '40+' end as carga_tramo,
    min(floor(carga_pct))                     as orden,
    count(*)                                  as creditos,
    sum(monto_otorgado)                       as monto,
    100.0 * avg(evento_12m::int)              as evento_12m_pct,
    100.0 * avg(tasa_inicial)                 as tasa_media_pct
from {{ ref('int_bondora__originacion') }}
group by 1
