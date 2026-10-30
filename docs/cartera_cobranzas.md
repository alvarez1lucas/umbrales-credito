# Cartera y cobranzas: resultados de la fase 2

Datos: dos fotos reales de la cartera completa de Bondora, con corte el **14-jul-2025** (capturada por la
Wayback Machine) y el **22-oct-2026**: 806.217 créditos después de excluir desistimientos, y 15 meses entre fotos.
Cartera viva a oct-26: 838 millones de euros. Los montos están en euros. Las cifras salen de `outputs/`.

## Qué se encontró

1. **La ventana de cobranza se cierra a los 60 días.** De los créditos en 1-30 días de atraso, 34% terminó en
   90+ o castigo 15 meses después; en 31-60, 61%; en 61-90, 84%. La cura cae de 44% a 23% y a 11%.
2. **Priorizar por pérdida esperada casi duplica la cobertura.** Con capacidad para el 20% de las cuentas,
   gestionar a los más atrasados cubre el 34% del saldo que termina mal; por pérdida esperada, el 57%.
   Casi toda la mejora viene del saldo: ordenar sólo por saldo ya llega al 53%.
3. **Lo que se recupera llega entre los 6 y los 24 meses.** Sobre el saldo en mora, el recupero real en 15 meses fue de
   15% si el evento tenía menos de 6 meses, 26-28% entre 6 y 24 meses, y 5,5% después de 36 meses.
4. **En Finlandia el riesgo no se cobra.** La tasa queda en ~18% de AA a F mientras la PD a 12 meses va de 3,0% a
   19,5%, y el margen ajustado cae de 15,5 a 5,4 puntos. Es consistente con el tope legal de tasa de Finlandia.
   En Estonia la tasa sube con el riesgo (19,7% a 30,5%) y el margen queda plano en 18-20 puntos.
5. **Dinamarca pierde plata en los ratings bajos.** PD a 12 meses de 25% a 43% con tasa de 18%: el margen ajustado
   queda negativo en C, D y G (hasta -11,5 puntos). Es el mercado donde conviene endurecer la política primero.
   La LGD de Dinamarca es la agregada, porque todavía no tiene eventos maduros.
6. **Las cosechas 2016-2019 apenas cubrieron su riesgo.** Con 57-59% de créditos en evento y más de un tercio del
   capital perdido, las de 2017 y 2019 cerraron con +1,3% y +0,5% sobre lo prestado, antes de fondeo y costos.
   Las cosechas posteriores mejoraron: de ~50% a ~30% de mora 90+ a 36 meses.
7. **La norma del BCRA previsiona poco lo sano y mucho lo muy viejo.** Sobre esta cartera, las previsiones mínimas
   suman 194 millones contra 239 de pérdida esperada. En situación 1, 1% contra 6,9%; en situación 5, 100% contra 86%.

| Situación BCRA | Saldo (M€) | Previsión BCRA (M€) | Pérdida esperada (M€) |
|---|---:|---:|---:|
| 1. Normal | 591,8 | 5,9 | 40,7 |
| 2. Riesgo bajo | 25,9 | 1,3 | 12,2 |
| 3. Riesgo medio | 20,4 | 5,1 | 17,4 |
| 4. Riesgo alto | 36,1 | 18,0 | 28,3 |
| 5. Irrecuperable | 163,3 | 163,3 | 140,4 |
| **Total** | **837,6** | **193,7** | **238,9** |

## Recomendaciones

- **Concentrar la gestión antes de los 60 días** y ordenar la cola por pérdida esperada, no por antigüedad.
- **Revisar precio o cupo por rating en Finlandia**: con la tasa limitada, el ajuste posible es de cupo y corte.
- **Endurecer la originación en Dinamarca** en los ratings C a G hasta ver mejora en las cosechas.
- **No extrapolar la LGD histórica sin más**: el recupero reciente apunta a una LGD de ~50%, contra 69% en eventos maduros.

## Cómo se calculó

- **Evento 90+:** ver [plan.md](plan.md). Fecha de corte de cada foto: inicio del atraso + días de atraso de los activos.
- **Transiciones:** tramo de cada crédito en jul-25 contra su tramo en oct-26. El horizonte es de 15 meses, no mensual.
- **Situaciones y previsiones:** textos ordenados del BCRA "Clasificación de deudores" (cartera de consumo: hasta 31, 90,
  180 y 365 días) y "Previsiones mínimas" (1%, 5%, 25%, 50% y 100% sin garantías preferidas).
- **Pérdida esperada, al estilo NIIF 9:** créditos al día, PD a 12 meses del segmento × LGD; de 1 a 90 días, probabilidad
  real de evento entre fotos × LGD; más de 90 días, saldo × (1 - recupero observado por antigüedad).
- **LGD:** 1 - recupero de capital de eventos con 36 meses o más, ponderado por exposición, con el saldo al evento
  estimado por cronograma francés. Encadenando el recupero real entre fotos da ~50%, que baja la pérdida esperada
  total de 239 a 225 millones.
- **Backtest de cobranza:** segmentos (tramo × saldo × país) calibrados en la mitad de los 26.348 créditos atrasados de jul-25
  y evaluados en la otra mitad, con su resultado real en oct-26.

## Escenario de canales (supuestos, no datos)

Bondora no publica gestiones y no hay grupo de control, así que **no se mide el efecto de gestionar**. Los costos, las
tasas de contacto, promesa y cumplimiento, la incrementalidad y el efecto por tramo son supuestos de
`config/settings.yaml`. Con esos supuestos, llamar conviene por encima de 221 € de saldo en 1-30 días, 247 € en 31-60 y
360 € en 61-90; con la mitad de contacto o el doble de costo, esos umbrales se duplican. Debajo de eso, WhatsApp.

## Limitaciones

- Dos fotos: la matriz muestra un solo período, y uno bueno o malo pesa entero. Crece con cada publicación.
- Los atrasos que se curaron antes de la foto no se ven, y las tasas de cosechas viejas son un piso.
- La LGD madura viene sobre todo de cosechas 2016-2022, y países sin eventos maduros usan la LGD agregada.
- El margen ajustado usa la pérdida del primer año, sin fondeo ni costos. El resultado de cosechas es nominal.
- La cobertura del backtest mide si la gestión llega a las cuentas que terminan mal, no si las salva.
- Son préstamos europeos: la comparación con la norma del BCRA es un ejercicio, no una previsión real de Bondora.
