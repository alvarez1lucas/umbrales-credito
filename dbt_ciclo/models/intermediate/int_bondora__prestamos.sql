-- Un crédito por fila, según la foto más reciente, con el evento de mora 90+ y su fecha.
--
-- Evento 90+: el crédito llegó a {{ var('dias_evento') }} días de atraso, o Bondora lo declaró en default
-- o lo pasó a pérdida. Fecha del evento: inicio del atraso + {{ var('dias_evento') }} días; si falta,
-- la foto menos los días de atraso que exceden {{ var('dias_evento') }}, y si no, la foto menos los meses en default. Un atraso que se curó y se pagó sin quedar marcado no se ve
-- en la foto: para las cosechas viejas la tasa es un piso.
with ultima as (
    select *
    from {{ ref('int_bondora__estados') }}
    qualify fecha_foto = max(fecha_foto) over (partition by prestamo_id)
),
eventos as (
    select
        *,
        (estado in ('castigado', 'default') or en_default or coalesce(dias_atraso, 0) >= {{ var('dias_evento') }}) as evento_90
    from ultima
)
select
    *,
    case when evento_90 then least(
        fecha_foto,
        coalesce(fecha_inicio_atraso + to_days({{ var('dias_evento') }}),
                 cast(fecha_foto - to_days(cast(dias_atraso as integer) - {{ var('dias_evento') }}) as date),
                 cast(fecha_foto - to_months(cast(round(coalesce(meses_en_default, 0)) as integer)) as date))
    ) end as fecha_evento_90,
    date_trunc('quarter', fecha_otorgamiento) as cosecha,
    -- Pérdida de capital: lo prestado que no volvió (sólo para créditos con evento)
    case when evento_90 then greatest(monto_otorgado - capital_pagado, 0) end as capital_no_recuperado
from eventos
