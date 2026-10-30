-- Estado y tramo de cada crédito en cada foto. Excluye desistimientos (devueltos dentro de los 14 días)
-- y créditos devueltos o en revisión, que nunca llegaron a ser cartera.
with base as (
    select *
    from {{ ref('stg_bondora__fotos') }}
    where not desistido_14_dias
      and estado_bondora in ('Active', 'Repaid', 'Defaulted')
      and estado_riesgo_bondora <> 'Cancelled'
)
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
