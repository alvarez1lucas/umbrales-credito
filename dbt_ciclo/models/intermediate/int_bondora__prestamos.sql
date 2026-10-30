-- Un crédito por fila, según la foto más reciente.
select
    *,
    date_trunc('quarter', fecha_otorgamiento) as cosecha,
    -- Pérdida de capital: lo prestado que no volvió (sólo para créditos con evento)
    case when evento_90 then greatest(monto_otorgado - capital_pagado, 0) end as capital_no_recuperado
from {{ ref('int_bondora__estados') }}
qualify fecha_foto = max(fecha_foto) over (partition by prestamo_id)
