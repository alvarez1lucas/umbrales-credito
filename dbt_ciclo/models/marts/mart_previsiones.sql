-- Previsiones sobre la cartera viva de la última foto: mínimo regulatorio del BCRA (situaciones 1 a 5,
-- sin garantías preferidas) contra pérdida esperada al estilo NIIF 9.
-- Etapa 1: al día, PD a 12 meses por segmento × LGD; 1 a 30 días, probabilidad real de terminar en evento
-- entre fotos × LGD. Etapa 2 (31 a 90): esa misma probabilidad × LGD. Etapa 3 (más de 90): saldo × (1 - recupero
-- observado entre fotos, por antigüedad). La probabilidad usa el primer par de fotos, el de horizonte más largo.
with viva as (
    select *, greatest(coalesce(dias_atraso, 0), 0) as dias
    from {{ ref('int_bondora__prestamos') }}
    where estado in ('activo', 'default') and saldo_capital > 0
),
transiciones as (
    select
        tramo_desde,
        100.0 * sum(creditos) filter (where tramo_hasta in ('90+', 'castigado')) / sum(creditos) as prob_evento_pct
    from {{ ref('mart_roll_rates') }}
    where tramo_desde in ('al_dia', '1-30', '31-60', '61-90')
      and fecha_desde = (select min(fecha_desde) from {{ ref('mart_roll_rates') }})
    group by 1
),
pd_pais as (
    select pais, sum(pd_12m_pct * creditos) / sum(creditos) as pd_12m_pct
    from {{ ref('mart_perdida_segmentos') }}
    group by 1
),
pd_global as (
    select sum(pd_12m_pct * creditos) / sum(creditos) as pd_12m_pct
    from {{ ref('mart_perdida_segmentos') }}
),
lgd_global as (
    select sum(lgd_pct * exposicion) / sum(exposicion) as lgd_pct
    from {{ ref('mart_lgd_pais') }}
),
recupero as (
    select antiguedad_evento, 100.0 * sum(capital_cobrado) / sum(saldo_inicial) as recupero_pct
    from {{ ref('mart_recupero_observado') }}
    group by 1
),
marcada as (
    select
        v.*,
        s.situacion,
        s.prevision_sin_garantia_pct,
        case when v.dias <= 30 then 1 when v.dias <= 90 then 2 else 3 end as etapa,
        coalesce(l.lgd_pct, lg.lgd_pct)                       as lgd,
        coalesce(ps.pd_12m_pct, pp.pd_12m_pct, pg.pd_12m_pct) as pd_12m,
        t.prob_evento_pct,
        {{ antiguedad_evento("date_diff('month', v.fecha_evento_90, v.fecha_foto)") }} as antiguedad_evento
    from viva v
    join {{ ref('bcra_situaciones') }} s on v.dias between s.dias_desde and s.dias_hasta
    cross join pd_global pg
    cross join lgd_global lg
    left join {{ ref('mart_lgd_pais') }} l on v.pais = l.pais
    left join {{ ref('mart_perdida_segmentos') }} ps on v.pais = ps.pais and v.rating = ps.rating
    left join pd_pais pp on v.pais = pp.pais
    left join transiciones t on v.tramo = t.tramo_desde
),
calculo as (
    select
        m.*,
        m.saldo_capital * m.prevision_sin_garantia_pct / 100.0 as prevision_bcra,
        case m.etapa
            when 1 then m.saldo_capital * (case when m.tramo = 'al_dia' then m.pd_12m else m.prob_evento_pct end) / 100.0 * m.lgd / 100.0
            when 2 then m.saldo_capital * m.prob_evento_pct / 100.0 * m.lgd / 100.0
            else m.saldo_capital * (1 - coalesce(r.recupero_pct, 0) / 100.0)
        end as perdida_esperada
    from marcada m
    left join recupero r on m.antiguedad_evento = r.antiguedad_evento
)
select
    fecha_foto, pais, situacion, etapa,
    count(*)              as creditos,
    sum(saldo_capital)    as saldo_capital,
    sum(prevision_bcra)   as prevision_bcra,
    sum(perdida_esperada) as perdida_esperada
from calculo
group by 1, 2, 3, 4
