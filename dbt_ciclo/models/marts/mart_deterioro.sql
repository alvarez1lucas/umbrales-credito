-- Mora 90+ a 12 meses por año de originación, país y rating. Sólo cuentan los créditos con 12 meses de antigüedad,
-- así la cosecha reciente no se subestima: muestra dónde y desde cuándo cambió el riesgo.
select
    cast(year(cosecha) as integer)                                      as cosecha_anio,
    pais,
    coalesce(rating, 'sin_rating')                                      as rating,
    count(*)                                                            as creditos,
    count(*) filter (where evento_90 and meses_hasta_evento <= 12)      as eventos_12m,
    sum(monto_otorgado)                                                 as monto
from {{ ref('fct_prestamos') }}
where cosecha >= date '2014-01-01' and edad_meses >= 12
group by 1, 2, 3
