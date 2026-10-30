-- Estado, tramo y evento 90+ de cada crédito en cada foto. Excluye desistimientos (devueltos dentro de
-- los 14 días) y créditos devueltos o en revisión, que nunca llegaron a ser cartera.
--
-- Evento 90+: el crédito llegó a {{ var('dias_evento') }} días de atraso, o Bondora lo declaró en default
-- o lo pasó a pérdida. Fecha del evento: inicio del atraso + {{ var('dias_evento') }} días; si falta,
-- la foto menos los días de atraso que exceden {{ var('dias_evento') }}, y si no, la foto menos los meses
-- en default. Un atraso que se curó y se pagó sin quedar marcado no se ve en la foto: para las cosechas
-- viejas la tasa es un piso.
with base as (
    select *
    from {{ ref('stg_bondora__fotos') }}
    where not desistido_14_dias
      and estado_bondora in ('Active', 'Repaid', 'Defaulted')
      and estado_riesgo_bondora <> 'Cancelled'
),
clasificados as (
    select
        *,
        case
            when estado_riesgo_bondora = 'Written Off' then 'castigado'
            when estado_bondora = 'Defaulted'          then 'default'
            when estado_bondora = 'Repaid'             then 'pagado'
            else 'activo'
        end as estado,
        -- Tramo sólo para la cartera viva; los cerrados quedan con su estado final
        case
            when estado_riesgo_bondora = 'Written Off' then 'castigado'
            when estado_bondora = 'Repaid'             then 'pagado'
            else {{ tramo_atraso('dias_atraso') }}
        end as tramo,
        date_diff('month', fecha_otorgamiento, fecha_foto) as edad_meses
    from base
),
eventos as (
    select
        *,
        (estado in ('castigado', 'default') or en_default or coalesce(dias_atraso, 0) >= {{ var('dias_evento') }}) as evento_90
    from clasificados
)
select
    *,
    case when evento_90 then least(
        fecha_foto,
        coalesce(fecha_inicio_atraso + to_days({{ var('dias_evento') }}),
                 cast(fecha_foto - to_days(cast(dias_atraso as integer) - {{ var('dias_evento') }}) as date),
                 cast(fecha_foto - to_months(cast(round(coalesce(meses_en_default, 0)) as integer)) as date))
    ) end as fecha_evento_90
from eventos
