-- Embudo de originación por año y producto: de la solicitud al desembolso.
select
    anio, producto_corto as producto, resultado,
    count(*)           as solicitudes,
    sum(monto)         as monto
from {{ ref('int_hmda__decisiones') }}
group by 1, 2, 3
