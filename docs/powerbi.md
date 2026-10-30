# Guía de Power BI

Cómo armar el tablero en Power BI Desktop con los CSV de `outputs/marts/` y `outputs/originacion/`. Son cuatro páginas y se arma
en una sesión. Al terminar, guardá el archivo como `powerbi/umbrales_credito.pbix` y exportá el PDF a `powerbi/umbrales_credito.pdf`.

## 1. Cargar los datos

Inicio → Obtener datos → Carpeta → `outputs/marts`. Combiná sólo si querés; lo más simple es cargar cada CSV por separado con
**Obtener datos → Texto/CSV**. Las cifras usan punto decimal: si tu Windows está en español, en Power Query usá
**Cambiar tipo → Usar configuración regional → Inglés (Estados Unidos)** en las columnas numéricas. Marcá como Fecha `cosecha`,
`fecha_foto`, `fecha_desde` y `fecha_hasta`.

## 2. Modelo en estrella

Cada mart es una tabla de hechos agregada. Creá estas relaciones (uno a varios, desde la dimensión):

| Dimensión | Campo | Tablas de hechos |
|---|---|---|
| `dim_tramo` | `tramo` | `mart_cartera_tramos[tramo]` |
| `dim_rating` | `rating` | `mart_cartera_tramos[rating]`, `mart_perdida_segmentos[rating]` |
| `dim_pais` | `pais` | `mart_cartera_tramos[pais]`, `mart_previsiones[pais]`, `mart_perdida_segmentos[pais]` |
| `dim_situacion` | `situacion` | `mart_previsiones[situacion]` |

Para `mart_roll_rates`, duplicá `dim_tramo` como `dim_tramo_desde` y `dim_tramo_hasta` y relacioná cada una con su columna.
En `dim_tramo` y `dim_rating`, ordená `tramo` y `rating` por la columna `orden` (Herramientas de columna → Ordenar por columna).

## 3. Medidas DAX

```dax
Saldo = SUM(mart_cartera_tramos[saldo_capital])
Créditos = SUM(mart_cartera_tramos[creditos])

PAR30 % =
DIVIDE(
    CALCULATE([Saldo], dim_tramo[tramo] IN {"31-60", "61-90", "90+"}),
    CALCULATE([Saldo], REMOVEFILTERS(dim_tramo))
)

PAR90 % =
DIVIDE(
    CALCULATE([Saldo], dim_tramo[tramo] = "90+"),
    CALCULATE([Saldo], REMOVEFILTERS(dim_tramo))
)

Previsión BCRA = SUM(mart_previsiones[prevision_bcra])
Pérdida esperada = SUM(mart_previsiones[perdida_esperada])
Saldo previsiones = SUM(mart_previsiones[saldo_capital])
Previsión BCRA % = DIVIDE([Previsión BCRA], [Saldo previsiones])
Pérdida esperada % = DIVIDE([Pérdida esperada], [Saldo previsiones])
Diferencia con la norma = [Pérdida esperada] - [Previsión BCRA]

Solicitudes = SUM(mart_embudo[solicitudes])
Otorgadas = CALCULATE([Solicitudes], mart_embudo[resultado] = "otorgado")
Rechazadas = CALCULATE([Solicitudes], mart_embudo[resultado] = "rechazado")
Con decisión =
CALCULATE([Solicitudes], mart_embudo[resultado] IN {"otorgado", "aprobado_no_aceptado", "rechazado"})
Tasa de rechazo = DIVIDE([Rechazadas], [Con decisión])

Rechazos = SUM(mart_motivos_rechazo[rechazos])
% de rechazos = DIVIDE([Rechazos], CALCULATE([Rechazos], ALL(mart_motivos_rechazo[motivo])))

Mora cosecha % =
DIVIDE(SUM(mart_cosechas[creditos_con_evento]), SUM(mart_cosechas[creditos]))

Roll % =
DIVIDE(
    SUM(mart_roll_rates[creditos]),
    CALCULATE(SUM(mart_roll_rates[creditos]), REMOVEFILTERS(dim_tramo_hasta))
)
```

Para las tablas que ya vienen en porcentaje (`aprobacion_pct`, `pd_12m_pct`, `margen_ajustado_pct`), usá el promedio ponderado
si agregás segmentos, no la suma:

```dax
PD 12m % (pond.) =
DIVIDE(
    SUMX(mart_perdida_segmentos, mart_perdida_segmentos[pd_12m_pct] * mart_perdida_segmentos[creditos]),
    SUM(mart_perdida_segmentos[creditos])
)
```

## 4. Páginas

**Resumen.** Tarjetas: Saldo, PAR30 %, PAR90 %, Tasa de rechazo, Pérdida esperada %. Una tabla con las cinco preguntas y su hallazgo
(cuadro de texto, copiado del memo). Segmentador de país.

**Originación.** Embudo con `resultado` y Solicitudes. Barras de `% de rechazos` por `motivo`. Líneas de `aprobacion_pct` por `dti`
(ordená por `dti_orden`) con `producto` como leyenda: es el gráfico del precipicio. Tabla de `simulacion_tope_dti.csv`.

**Cartera.** Líneas de Mora cosecha % por `mes`, con `cosecha` (año) como leyenda. Matriz de Roll % con `dim_tramo_desde` en filas y
`dim_tramo_hasta` en columnas, con formato condicional. Dispersión de `pd_12m_pct` contra `tasa_media_pct` por rating, con país como leyenda.
Previsión BCRA % y Pérdida esperada % por situación, en barras agrupadas.

**Cobranzas.** Líneas de `saldo_malo_cubierto_pct` por `capacidad_pct`, con `regla` como leyenda (`backtest_priorizacion.csv`). Barras apiladas de
Roll % por tramo. Tabla de `escenario_canales.csv`, con el título **"Escenario con supuestos, no datos observados"**.

## 5. Antes de publicar

- Títulos que digan la conclusión, no la variable: "La aprobación cae al cruzar 50", no "Aprobación por DTI".
- Un solo eje por gráfico, y el mismo color para el mismo país o regla en todas las páginas.
- Rotulá los supuestos en la misma página donde aparecen.
