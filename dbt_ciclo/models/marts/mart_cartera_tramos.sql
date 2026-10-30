-- Cartera viva (activos y en default sin castigar) por foto, país, rating y tramo de atraso.
select
    fecha_foto, pais, coalesce(rating, 'sin_rating') as rating, tramo,
    count(*)            as creditos,
    sum(saldo_capital)  as saldo_capital
from {{ ref('int_bondora__estados') }}
where estado in ('activo', 'default')
group by 1, 2, 3, 4
