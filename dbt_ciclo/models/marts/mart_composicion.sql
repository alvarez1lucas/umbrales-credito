-- Composición de la cartera viva por foto, país, rating y plazo, con su atraso: permite ver concentración y dónde cambió el riesgo entre fotos.
select
    fecha_foto, pais, coalesce(rating, 'sin_rating') as rating,
    case when plazo_meses <= 24 then 'Hasta 24'
         when plazo_meses <= 36 then '25-36'
         when plazo_meses <= 48 then '37-48'
         when plazo_meses <= 60 then '49-60'
         else 'Más de 60' end                                           as plazo,
    case when plazo_meses <= 24 then 1 when plazo_meses <= 36 then 2 when plazo_meses <= 48 then 3
         when plazo_meses <= 60 then 4 else 5 end                       as plazo_orden,
    count(*)                                                            as creditos,
    sum(saldo_capital)                                                  as saldo_capital,
    coalesce(sum(saldo_capital) filter (where tramo in ('31-60', '61-90', '90+')), 0) as saldo_par30,
    coalesce(sum(saldo_capital) filter (where tramo = '90+'), 0)        as saldo_par90
from {{ ref('int_bondora__estados') }}
where estado in ('activo', 'default')
group by 1, 2, 3, 4, 5
