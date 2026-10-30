{# Tramo de atraso estándar a partir de los días de atraso (nulo = al día). #}
{% macro tramo_atraso(dias) -%}
    case
        when coalesce({{ dias }}, 0) <= 0  then 'al_dia'
        when {{ dias }} <= 30 then '1-30'
        when {{ dias }} <= 60 then '31-60'
        when {{ dias }} <= 90 then '61-90'
        else '90+'
    end
{%- endmacro %}
