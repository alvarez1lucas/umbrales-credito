-- Solicitudes de compra de vivienda propia con primer gravamen: el universo comparable de política.
-- `grupo` combina etnia y raza como se reporta en análisis de préstamo justo: Hispano primero y, entre los
-- no hispanos, la raza declarada. Las solicitudes conjuntas o sin dato quedan aparte.
select
    *,
    split_part(producto, ':', 1) as producto_corto,
    resultado in ('otorgado', 'aprobado_no_aceptado', 'rechazado') as con_decision,
    resultado in ('otorgado', 'aprobado_no_aceptado')              as aprobado,
    case
        when etnia = 'Hispanic or Latino' then 'Hispano'
        when etnia = 'Not Hispanic or Latino' and raza = 'White' then 'Blanco'
        when etnia = 'Not Hispanic or Latino' and raza = 'Black or African American' then 'Negro'
        when etnia = 'Not Hispanic or Latino' and raza = 'Asian' then 'Asiático'
        when etnia = 'Joint' or raza = 'Joint' then 'Conjunta'
        when etnia = 'Ethnicity Not Available' or raza = 'Race Not Available' then 'Sin dato'
        else 'Otros'
    end as grupo,
    case
        when ltv is null  then null
        when ltv <= 80    then '<=80'
        when ltv <= 90    then '80-90'
        when ltv <= 95    then '90-95'
        when ltv <= 100   then '95-100'
        else '>100'
    end as ltv_tramo
from {{ ref('stg_hmda__solicitudes') }}
where gravamen = 1 and ocupacion = 1
