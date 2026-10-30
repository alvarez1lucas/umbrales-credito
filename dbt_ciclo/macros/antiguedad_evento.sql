{# Tramo de antigüedad desde el evento 90+, en meses. #}
{% macro antiguedad_evento(meses) -%}
    case
        when {{ meses }} < 6  then '0-6'
        when {{ meses }} < 12 then '6-12'
        when {{ meses }} < 24 then '12-24'
        when {{ meses }} < 36 then '24-36'
        else '36+'
    end
{%- endmacro %}
