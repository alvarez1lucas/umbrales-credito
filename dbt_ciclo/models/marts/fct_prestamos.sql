-- Tabla de hechos de créditos: una fila por crédito con atributos de originación y desempeño.
select
    prestamo_id, pais, rating, fecha_otorgamiento, cosecha, monto_otorgado, tasa_inicial, plazo_meses, ingreso,
    fecha_foto, estado, tramo, dias_atraso, saldo_capital, capital_pagado, intereses_pagados, punitorios_pagados,
    total_cobrado, evento_90, fecha_evento_90,
    case when evento_90 then date_diff('month', fecha_otorgamiento, fecha_evento_90) end as meses_hasta_evento,
    capital_no_recuperado, edad_meses
from {{ ref('int_bondora__prestamos') }}
