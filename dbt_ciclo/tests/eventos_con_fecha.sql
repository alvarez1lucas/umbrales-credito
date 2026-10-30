-- Todo crédito con evento 90+ tiene fecha de evento, posterior al otorgamiento y no posterior a la foto.
select prestamo_id
from {{ ref('fct_prestamos') }}
where evento_90 and (fecha_evento_90 is null or fecha_evento_90 > fecha_foto or fecha_evento_90 < fecha_otorgamiento)
