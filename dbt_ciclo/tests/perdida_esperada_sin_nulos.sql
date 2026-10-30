-- Toda la cartera viva tiene pérdida esperada, y nunca mayor que su saldo.
select pais, situacion, etapa
from {{ ref('mart_previsiones') }}
where perdida_esperada is null or perdida_esperada > saldo_capital
