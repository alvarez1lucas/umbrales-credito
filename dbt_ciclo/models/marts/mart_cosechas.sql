-- Curvas de cosecha: % acumulado de créditos (y de monto) con evento 90+ según los meses desde el
-- otorgamiento, por trimestre de originación. En cada mes sólo cuentan los créditos que ya tienen esa
-- antigüedad en la foto, así las cosechas recientes no se subestiman.
with meses as (
    select unnest(generate_series(1, {{ var('meses_curva') }})) as mes
),
base as (
    select p.cosecha, m.mes, p.monto_otorgado,
           (p.evento_90 and p.meses_hasta_evento <= m.mes) as con_evento
    from {{ ref('fct_prestamos') }} p
    join meses m on p.edad_meses >= m.mes
    where p.cosecha >= date '2014-01-01'
)
select
    cosecha,
    mes,
    count(*)                                                        as creditos,
    count(*) filter (where con_evento)                              as creditos_con_evento,
    100.0 * count(*) filter (where con_evento) / count(*)           as tasa_evento_pct,
    100.0 * sum(monto_otorgado) filter (where con_evento) / sum(monto_otorgado) as tasa_evento_monto_pct
from base
group by cosecha, mes
having count(*) >= 200
order by cosecha, mes
