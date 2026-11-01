# Simulador de política en Excel

`excel/simulador_politica.xlsx` (y `_en` en inglés) permite mover una regla de crédito y ver al instante qué pasa con la aprobación, la mora
y el resultado. `python -m ciclo.excel` lo genera desde `outputs/originacion/`.

## Qué tiene

| Hoja | Para qué sirve | Funciones |
|---|---|---|
| Supuestos | Costo, escenario y LGD por país | Listas de validación, `INDEX`, `MATCH` |
| Datos | Tabla `tblSegmentos` por año, país, rating y carga, con la decisión de cada segmento | Tabla de Excel, fórmulas por fila |
| Simulador | Reglas, comparación contra la cartera actual, resultado por rating y gráfico | `SUMIFS`, formato condicional |
| Conciliación | Compara cada regla con Python en resultado, aprobación y mora, y corre cinco controles internos | `SUMIFS`, `COUNTIF`, control de estado |
| Sensibilidad | Costo de equilibrio y grillas de costo contra LGD y mora | Referencias mixtas |
| Resumen | Mora por rating y año, monto por país | `SUMIFS` con varias condiciones, escala de color |

## Decisiones

- **Funciones de Excel 2016:** `INDEX` + `MATCH` en lugar de `XLOOKUP`, porque un banco puede tener una versión vieja.
- **Conciliación visible:** el archivo demuestra que reproduce las seis reglas del proyecto con diferencias menores a 1 €, y también su aprobación y su mora.
- **Controles internos:** los totales por rating y país deben sumar el total, y la decisión debe coincidir con la regla.
- **Supuestos validados:** el costo y la LGD no aceptan valores fuera de 0% a 100%, y los multiplicadores deben ser positivos.
- **Costo de equilibrio:** muestra desde qué costo una regla gana plata. Es la cifra que define si conviene endurecer.
- **Sólo endurecer:** hay datos de créditos otorgados, no de rechazados, así que no se puede evaluar relajar una regla.

## Verificación

Las fórmulas se calculan con `formulas`, un motor independiente de Excel, y se compararon con pandas en la regla por defecto y en otras
combinaciones de reglas, costo y escenario. El archivo abre en Excel 2016. Las tablas dinámicas no están incluidas: se arman en Excel como práctica.
