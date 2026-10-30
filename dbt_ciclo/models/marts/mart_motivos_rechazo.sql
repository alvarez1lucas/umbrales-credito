-- Motivo principal de rechazo por año, producto y tramo de deuda-ingreso.
select
    d.anio, d.producto_corto as producto, coalesce(d.dti_tramo, 'sin_dato') as dti_tramo,
    coalesce(m.motivo, 'Sin motivo informado') as motivo,
    count(*) as rechazos
from {{ ref('int_hmda__decisiones') }} d
left join {{ ref('hmda_motivos_rechazo') }} m on d.motivo_rechazo_1 = m.motivo_codigo
where d.resultado = 'rechazado'
group by 1, 2, 3, 4
