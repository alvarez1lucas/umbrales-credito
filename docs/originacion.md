# Originación y política de crédito: resultados de la fase 3

Datos: **HMDA**, 519.998 solicitudes de compra de vivienda propia con primer gravamen en Georgia, EE.UU., 2023-2025
(405.589 con decisión), y **Bondora**, 308.050 créditos de consumo otorgados entre sep-23 y oct-25, con su resultado real a
12 meses. Ninguna fuente alcanza sola: HMDA ve a los rechazados pero no qué pasó después; Bondora ve el resultado pero
sólo de los otorgados. Las cifras salen de `outputs/originacion/`.

## Qué se encontró

1. **Más de una de cada cinco solicitudes se cae sin decisión.** De cada 100, 63 se otorgan, 18 desisten, 12 se rechazan, 4 quedan
   incompletas y 2 se aprueban pero no se aceptan.
2. **Dos motivos explican casi dos tercios de los rechazos:** deuda sobre ingreso (34%) e historial crediticio (30%).
3. **La regla se ve en los datos.** En créditos convencionales la aprobación es plana en ~91% hasta deuda-ingreso de 49, y cae a 28%
   en 50-60 y a 2% arriba de 60. En 49 se amontonan las solicitudes (15.544 contra ~9.000 en los valores vecinos): la huella del
   límite. En FHA, con garantía pública, sigue en 88% hasta 60 y recién ahí cae a 3%.
4. **Por debajo del límite, la deuda-ingreso casi no diferencia.** La aprobación no cambia entre 20 y 49, y el spread mediano sube
   sólo de 0,10 a 0,25 puntos. Por encima sube a 0,78 y 2,11: el mercado cobra el riesgo donde está la regla.
5. **Bajar el tope cuesta mucho más volumen de lo que parece.** De 49 a 45, se pierde el 21% de los aprobados; a 43, el 29%.
6. **El mismo tope no afecta igual a todos.** Con tope de 45 sale el 28% de los aprobados negros e hispanos contra 17% de los
   blancos. El índice de impacto adverso (umbral de atención: 0,80) empeora para solicitantes negros de 0,77 a 0,68 y deja
   a los hispanos en 0,81; con tope de 43 quedan en 0,64 y 0,76.
7. **La brecha de rechazo se achica al controlar, pero no desaparece.** Para solicitantes negros contra blancos baja de 11,4 a
   6,2 puntos (IC 95%: 4,8 a 7,5) con perfil, producto y prestamista; para hispanos, de 4,8 a 2,7 (1,9 a 3,5). Para asiáticos
   cambia de signo: de -2,4 a +2,0 (1,2 a 2,8). **No prueba discriminación:** faltan el score y el resultado del motor de decisión.
8. **Tope de carga en Bondora: no paga.** La mora a 12 meses sube con la carga (de 7,8% a 25,9%), pero muy pocos créditos están
   altos y al recortarlos se pierde resultado en todos los topes probados.
9. **Rating y país sí pagan, con un costo supuesto de 10 puntos.** Sacar Dinamarca y Letonia mejora el resultado en 0,53 M€ (IC 95%:
   0,44 a 0,63) resignando el 3% de los créditos; sacar E a G logra lo mismo (0,55 M€) resignando el 10%. Sin ese costo, ninguna
   regla mejora el resultado: el negocio del primer año se decide en el costo de fondeo y operación.
10. **Una regla no vale lo mismo en todo momento.** Dinamarca y Letonia perdieron en todos los semestres. Los ratings F-G pasaron de
    +8,3% a -9,7% del monto entre fines de 2023 y 2025: una regla calibrada con las cosechas viejas no los habría sacado.

| Tope de deuda-ingreso (convencional) | Aprobación | Aprobados perdidos | Monto perdido | Impacto adverso, negros | Impacto adverso, hispanos |
|---:|---:|---:|---:|---:|---:|
| Sin tope nuevo | 82,2% | - | - | 0,77 | 0,93 |
| 49 | 81,0% | 1,4% | 1,2% | 0,76 | 0,92 |
| 47 | 71,6% | 13,0% | 12,1% | 0,71 | 0,85 |
| 45 | 65,2% | 20,7% | 19,5% | 0,68 | 0,81 |
| 43 | 58,3% | 29,1% | 27,8% | 0,64 | 0,76 |
| 40 | 47,9% | 41,7% | 40,8% | 0,59 | 0,70 |

| Regla en Bondora (costo supuesto: 10 pp) | Créditos que quedan | Mora a 12 meses | Cambio en resultado (M€) | IC 95% |
|---|---:|---:|---:|---:|
| Sin cambios | 100,0% | 8,2% | - | - |
| Sin Dinamarca ni Letonia | 97,0% | 7,6% | +0,53 | +0,44 a +0,63 |
| Sin ratings E a G | 90,0% | 7,3% | +0,55 | +0,42 a +0,68 |
| Sin ratings F y G | 95,7% | 7,8% | +0,26 | +0,18 a +0,33 |
| Carga de 15% o menos | 98,8% | 8,2% | -0,42 | -0,63 a -0,19 |
| Carga de 10% o menos | 96,6% | 8,1% | -1,44 | -1,74 a -1,12 |

## Recomendaciones

- **No bajar el tope de deuda-ingreso a ciegas:** por debajo de 50 la variable casi no separa aprobación ni precio, y el costo en
  volumen e impacto adverso es alto. Cualquier cambio necesita primero un análisis con desempeño real.
- **Si se relaja, medir antes:** 2.369 solicitudes convencionales de 50-60 se rechazaron sólo por esa razón; aprobarlas agrega 1 punto
  de aprobación, y su riesgo no se puede medir con HMDA.
- **Antes de aplicar una regla, medir su impacto adverso** y buscar la alternativa que logre el objetivo con menos impacto.
- **En Bondora, salir de los segmentos que pierden siempre** antes que tocar la carga, y **monitorear F-G** por semestre.

## Cómo se calculó

- **Universo HMDA:** primer gravamen y vivienda propia. Aprobación = (otorgados + aprobados no aceptados) / solicitudes con decisión.
- **Topes:** rechazan a los aprobados por encima del valor; quien no informa deuda-ingreso no cambia. Se aplican sobre convencionales.
- **Impacto adverso:** tasa de aprobación del grupo sobre la de solicitantes blancos no hispanos. La regla de los 4/5 es una
  señal de atención, no un veredicto.
- **Brecha condicional:** probabilidad lineal de rechazo con deuda-ingreso, LTV, ingreso, monto, producto y año, y efectos fijos de
  prestamista; errores agrupados por prestamista. Las solicitudes sin datos quedan con categoría propia, porque son sobre todo
  rechazadas y sacarlas sesgaba la comparación.
- **Resultado en Bondora:** por crédito, monto × (tasa - costo) - evento × LGD × monto. Intervalos por bootstrap de los créditos que salen.

## Limitaciones

- HMDA público no trae score crediticio ni desempeño. Los topes miden aprobación y volumen, no la mora que se evita.
- Georgia es un solo estado y son hipotecas: la mecánica se traslada, los números no.
- Las reglas de Bondora sólo se pueden evaluar endureciendo: los rechazados no se observan.
- El resultado mira el primer año de créditos de hasta 7 años, y el costo de 10 puntos es un supuesto.
- La exposición usa el monto otorgado, lo que exagera un poco la pérdida.
- Las reglas sobre Dinamarca y Letonia salieron de mirar estos mismos datos: su estabilidad por semestre ayuda, pero no reemplaza
  una prueba con cosechas nuevas.
