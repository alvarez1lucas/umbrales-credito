-- Recupero real entre dos fotos: capital y total cobrado sobre los créditos que en la primera foto ya
-- tenían evento 90+, según cuántos meses llevaban desde el evento. No depende del cronograma estimado.
with pares as (
    select
        a.fecha_foto as fecha_desde,
        b.fecha_foto as fecha_hasta,
        a.prestamo_id,
        a.pais,
        a.saldo_capital,
        date_diff('month', a.fecha_evento_90, a.fecha_foto) as meses_desde_evento,
        b.capital_pagado - a.capital_pagado as capital_cobrado,
        b.total_cobrado - a.total_cobrado   as total_cobrado_periodo
    from {{ ref('int_bondora__estados') }} a
    join {{ ref('int_bondora__estados') }} b
      on a.prestamo_id = b.prestamo_id and b.fecha_foto > a.fecha_foto
    where a.evento_90 and a.estado in ('default', 'activo') and a.saldo_capital > 0
),
tramos as (
    select *, {{ antiguedad_evento('meses_desde_evento') }} as antiguedad_evento
    from pares
)
select
    fecha_desde, fecha_hasta, pais, antiguedad_evento,
    count(*)                                                as creditos,
    sum(saldo_capital)                                      as saldo_inicial,
    sum(capital_cobrado)                                    as capital_cobrado,
    sum(total_cobrado_periodo)                              as total_cobrado,
    100.0 * sum(capital_cobrado) / sum(saldo_capital)       as recupero_capital_pct,
    100.0 * sum(total_cobrado_periodo) / sum(saldo_capital) as recupero_total_pct
from tramos
group by 1, 2, 3, 4
