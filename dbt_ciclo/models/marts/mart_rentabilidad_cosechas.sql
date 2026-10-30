-- Rentabilidad realizada de cosechas ya vencidas, por año y país: lo cobrado contra lo prestado.
-- Sólo créditos de hasta 60 meses con al menos 12 meses después del vencimiento, y cosechas hasta 2020:
-- en las posteriores sólo llegan a ese punto los plazos cortos y dejan de ser comparables.
-- Es un resultado nominal sobre el monto prestado: antes de fondeo y costos, y sin descontar el tiempo.
select
    year(fecha_otorgamiento)                                                        as cosecha_anio,
    pais,
    count(*)                                                                        as creditos,
    sum(monto_otorgado)                                                             as monto,
    100.0 * avg(tasa_inicial)                                                       as tasa_media_pct,
    100.0 * count(*) filter (where evento_90) / count(*)                            as evento_90_pct,
    100.0 * sum(greatest(monto_otorgado - capital_pagado, 0)) / sum(monto_otorgado) as capital_perdido_pct,
    100.0 * sum(intereses_pagados + punitorios_pagados) / sum(monto_otorgado)       as intereses_cobrados_pct,
    100.0 * sum(comisiones_pagadas) / sum(monto_otorgado)                           as comisiones_cobradas_pct,
    100.0 * sum(total_cobrado - monto_otorgado) / sum(monto_otorgado)               as resultado_pct
from {{ ref('int_bondora__prestamos') }}
where plazo_meses <= 60
  and edad_meses >= plazo_meses + 12
  and year(fecha_otorgamiento) between 2014 and 2020
group by 1, 2
having count(*) >= 200
