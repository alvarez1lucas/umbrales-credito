-- Una fila por solicitud hipotecaria, con el resultado y las variables de política en español.
select
    activity_year                                   as anio,
    state_code                                      as estado,
    lei                                             as prestamista_lei,
    "derived_msa-md"                                as msa,
    derived_loan_product_type                       as producto,
    action_taken                                    as resultado_codigo,
    case action_taken
        when 1 then 'otorgado' when 2 then 'aprobado_no_aceptado' when 3 then 'rechazado'
        when 4 then 'desistido' when 5 then 'incompleto' end as resultado,
    loan_amount                                     as monto,
    try_cast(loan_to_value_ratio as double)         as ltv,
    try_cast(interest_rate as double)               as tasa,
    try_cast(rate_spread as double)                 as spread,
    try_cast(loan_term as integer)                  as plazo_meses,
    try_cast(property_value as double)              as valor_propiedad,
    income                                          as ingreso_miles,
    debt_to_income_ratio                            as dti_reportado,
    -- DTI en tramos comparables: HMDA informa rangos salvo entre 36% y 49%, donde da el valor exacto
    case
        when debt_to_income_ratio in ('<20%')                then '<20'
        when debt_to_income_ratio in ('20%-<30%')            then '20-30'
        when debt_to_income_ratio in ('30%-<36%')            then '30-36'
        when try_cast(debt_to_income_ratio as integer) between 36 and 42 then '36-43'
        when try_cast(debt_to_income_ratio as integer) between 43 and 49 then '43-50'
        when debt_to_income_ratio in ('50%-60%')             then '50-60'
        when debt_to_income_ratio in ('>60%')                then '>60'
    end                                             as dti_tramo,
    try_cast(debt_to_income_ratio as integer)       as dti_exacto,
    derived_race                                    as raza,
    derived_ethnicity                               as etnia,
    derived_sex                                     as sexo,
    applicant_age                                   as edad,
    "denial_reason-1"                               as motivo_rechazo_1,
    "denial_reason-2"                               as motivo_rechazo_2,
    tract_minority_population_percent               as pct_minorias_zona,
    tract_to_msa_income_percentage                  as ingreso_zona_vs_msa
from {{ source('hmda', 'solicitudes') }}
