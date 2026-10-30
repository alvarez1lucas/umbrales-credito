{# Falla si alguna combinación de columnas se repite. #}
{% test combinacion_unica(model, columnas) %}
select {{ columnas | join(', ') }}, count(*) as n
from {{ model }}
group by {{ columnas | join(', ') }}
having count(*) > 1
{% endtest %}
