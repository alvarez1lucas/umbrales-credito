-- Una curva de cosecha acumulada no puede bajar más de lo que explica el cambio de población
-- (en cada mes cuentan sólo los créditos con esa antigüedad). Tolerancia: 1 punto.
select cosecha, mes, tasa_evento_pct, anterior
from (
    select cosecha, mes, tasa_evento_pct,
           lag(tasa_evento_pct) over (partition by cosecha order by mes) as anterior
    from {{ ref('mart_cosechas') }}
)
where tasa_evento_pct < anterior - 1
