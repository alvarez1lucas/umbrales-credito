# Tablero de Power BI

El tablero no se arma a mano: `python -m ciclo.powerbi` lo genera desde `outputs/` como proyecto de texto (formato PBIP, con el modelo en
TMDL y las páginas en PBIR), en español y en inglés. Requiere Power BI Desktop de septiembre de 2026 o posterior.

## Abrirlo

1. Abrí `powerbi/umbrales_credito.pbip`, o `powerbi/umbrales_credito_en.pbip` para inglés. Si Git clonó el repo en otra carpeta, corré antes `python -m ciclo.powerbi`: fija la ruta de los CSV en el parámetro `RutaDatos`.
2. Tocá **Actualizar**: el proyecto guarda la definición, no los datos.
3. Los `.pbix` de `powerbi/` son la versión lista para ver. Si se agregan `umbrales_credito.pdf` y `umbrales_credito_en.pdf`, el README y el sitio los enlazan solos.

Cuando cambian los datos, se corre `python -m ciclo.powerbi` con Power BI cerrado y se vuelven a exportar los PDF y los `.pbix`: los títulos llevan
cifras generadas desde `outputs/`, y esos archivos son una foto con fecha.

## Qué tiene

| Página | Pregunta | Contenido |
|---|---|---|
| Resumen | Todas | Cinco indicadores, selector de país y los hallazgos del README |
| Originación | Dónde está la regla | Aprobación por deuda-ingreso, resultados, motivos de rechazo y simulación de topes |
| Política | Qué pasa si la muevo | Cambio de resultado por regla, con y sin costo, intervalos y estabilidad por semestre |
| Cartera | Cómo está la cartera | Cosechas, transiciones entre tramos, riesgo contra tasa por segmento y previsiones |
| Deterioro | Dónde se deteriora y desde cuándo | Mora por cosecha y rating o país, concentración, cambio de PAR30 entre fotos y plazo |
| Cobranzas | A quién gestionar primero | Priorización comparada, destino de cada tramo, resultado por tramo y escenario de canales |
| Canales y plan | Por qué canal y cuánto rinde | Pérdida evitada con el mismo equipo, rendimiento por euro, supuestos del embudo y umbral para llamar |

## Dos idiomas

Son dos proyectos con los mismos datos y las mismas medidas; cambian títulos, ejes, notas, categorías y nombres de medidas. Las traducciones
propias de Power BI no sirven acá porque sólo funcionan en el servicio online, y un botón de idioma obligaría a volver dinámico cada texto.

## Decisiones del modelo

- **Modelo en estrella:** `dim_tramo`, `dim_rating`, `dim_pais` y `dim_situacion`, y dos copias de `dim_tramo` para el origen y el destino de las transiciones.
- **Una sola foto:** saldo y previsiones usan la foto más reciente. Sumar fotos de una cartera duplica el saldo.
- **Promedios ponderados:** PD y tasa se ponderan por créditos, y la aprobación se recalcula desde sus conteos. Promediar porcentajes de segmentos distintos da otro número.
- **Cosechas comparables:** un año sólo se muestra en los meses que observaron todos sus trimestres. Si no, el final de la curva mezcla cosechas distintas.
- **Barras en vez de embudo:** los resultados de una solicitud son excluyentes, no etapas.
- **FSA/RHS fuera del gráfico de aprobación:** con tan pocos casos por tramo, oscila entre 0 y 100%. Sigue en las demás tablas.
- **Supuestos rotulados:** el escenario de canales lo dice en el título, y la norma BCRA se aclara como ejercicio sobre una cartera europea.
