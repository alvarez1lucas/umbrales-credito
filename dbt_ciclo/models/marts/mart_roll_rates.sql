-- Roll rates: a qué tramo pasa cada crédito entre una foto y la siguiente. Crece con cada publicación
-- de Bondora que guarda el workflow mensual; con una sola foto queda vacía.
with secuencia as (
    select
        prestamo_id, fecha_foto, tramo, saldo_capital,
        lead(fecha_foto) over (partition by prestamo_id order by fecha_foto) as fecha_siguiente,
        lead(tramo)      over (partition by prestamo_id order by fecha_foto) as tramo_siguiente
    from {{ ref('int_bondora__estados') }}
)
select
    fecha_foto                as fecha_desde,
    fecha_siguiente           as fecha_hasta,
    tramo                     as tramo_desde,
    tramo_siguiente           as tramo_hasta,
    count(*)                  as creditos,
    sum(saldo_capital)        as saldo_desde,
    100.0 * count(*) / sum(count(*)) over (partition by fecha_foto, fecha_siguiente, tramo) as pct_del_tramo
from secuencia
where fecha_siguiente is not null
  and tramo not in ('pagado', 'castigado')
group by 1, 2, 3, 4
