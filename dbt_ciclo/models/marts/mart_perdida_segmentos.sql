-- Pérdida esperada anual y margen ajustado por riesgo por país y rating.
-- PD a 12 meses observada en créditos con al menos 12 meses de antigüedad (el rating existe desde fines
-- de 2023). LGD por país; los países sin eventos maduros usan la LGD agregada (lgd_fuente = 'agregada').
-- El margen es tasa - pérdida esperada del primer año: no descuenta fondeo ni costos.
with pd_seg as (
    select
        pais, rating,
        count(*)            as creditos,
        avg(tasa_inicial)   as tasa_media,
        sum(monto_otorgado) as monto,
        100.0 * count(*) filter (where evento_90 and date_diff('month', fecha_otorgamiento, fecha_evento_90) <= 12) / count(*) as pd_12m_pct
    from {{ ref('int_bondora__prestamos') }}
    where rating is not null and edad_meses >= 12
    group by 1, 2
    having count(*) >= 200
)
, lgd_agregada as (
    select sum(lgd_pct * exposicion) / sum(exposicion) as lgd_pct
    from {{ ref('mart_lgd_pais') }}
),
con_lgd as (
    select s.*, coalesce(l.lgd_pct, a.lgd_pct) as lgd_pct,
           case when l.lgd_pct is null then 'agregada' else 'pais' end as lgd_fuente
    from pd_seg s
    cross join lgd_agregada a
    left join {{ ref('mart_lgd_pais') }} l on s.pais = l.pais
)
select
    pais, rating, creditos, monto,
    100.0 * tasa_media                              as tasa_media_pct,
    pd_12m_pct,
    lgd_pct,
    lgd_fuente,
    pd_12m_pct * lgd_pct / 100.0                    as perdida_esperada_pct,
    100.0 * tasa_media - pd_12m_pct * lgd_pct / 100.0 as margen_ajustado_pct
from con_lgd
