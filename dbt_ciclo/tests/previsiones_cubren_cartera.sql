-- El saldo de mart_previsiones tiene que ser toda la cartera viva: nadie se cae del cruce con las situaciones.
select *
from (
    select
        (select sum(saldo_capital) from {{ ref('mart_previsiones') }}) as en_previsiones,
        (select sum(saldo_capital) from {{ ref('int_bondora__prestamos') }}
         where estado in ('activo', 'default') and saldo_capital > 0) as en_cartera
)
where abs(en_previsiones - en_cartera) > 1
