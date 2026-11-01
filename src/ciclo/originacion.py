"""Originación: qué pasa con la aprobación, la mora y el margen si muevo una regla, y a quién afecta.

`python -m ciclo.originacion` escribe outputs/originacion/.

Dos fuentes que se complementan, porque ninguna alcanza sola:
- HMDA tiene las solicitudes rechazadas, pero no qué pasó después con los créditos. Sirve para el efecto de
  un tope de deuda-ingreso sobre aprobación, volumen y spread, y para medir a quién afecta.
- Bondora tiene el resultado real a 12 meses, pero sólo de los créditos que se otorgaron. Sirve para el
  efecto de endurecer una regla sobre mora y margen; no permite evaluar relajarla.

Préstamo justo: índice de impacto adverso (aprobación de cada grupo sobre la del grupo de referencia, con la
regla de los 4/5 como señal de atención) y brecha de rechazo condicional, por mínimos cuadrados con efectos
fijos de prestamista. HMDA público no trae el score crediticio ni el resultado del motor de decisión, así
que la brecha condicional no prueba discriminación: mide cuánto queda sin explicar por lo observable.
"""

from __future__ import annotations

import json

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

from ciclo.config import path, settings

REFERENCIA = "Blanco"
GRUPOS = ["Negro", "Hispano", "Asiático"]
ORDEN_TRAMO = {"<20": 15, "20-30": 25, "30-36": 33, "50-60": 55, ">60": 65}
SIN_TOPE = 999  # fila de referencia: la política actual, sin ningún tope nuevo


# --------------------------------------------------------------------------- HMDA

def solicitudes(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.sql("""select prestamista_lei, anio, producto_corto as producto, grupo, resultado, aprobado, monto, spread,
                           ingreso_miles, ltv, ltv_tramo, dti_tramo, dti_exacto, motivo_rechazo_1, motivo_rechazo_2
                    from int_hmda__decisiones where con_decision""").df()
    df["dti_orden"] = df["dti_exacto"].astype("float").fillna(df["dti_tramo"].map(ORDEN_TRAMO))
    return df


def aplicar_tope(df: pd.DataFrame, tope: float) -> pd.Series:
    """Aprobados que siguen aprobados con un tope de deuda-ingreso. Los que no informan el dato no cambian."""
    return df["aprobado"] & ~(df["dti_orden"] > tope)


def impacto_adverso(df: pd.DataFrame, aprobado: pd.Series) -> dict[str, float]:
    """Aprobación de cada grupo sobre la del grupo de referencia."""
    tasas = aprobado.groupby(df["grupo"]).mean()
    return {g: float(tasas[g] / tasas[REFERENCIA]) for g in GRUPOS}


def simular_topes(df: pd.DataFrame, topes: list[float]) -> pd.DataFrame:
    base = df["aprobado"]
    filas = []
    for tope in topes:
        ap = aplicar_tope(df, tope)
        perdidos = base & ~ap
        ingreso_spread = (df["spread"].clip(lower=0).fillna(0) / 100 * df["monto"])
        filas.append({"tope_dti": tope, "aprobacion_pct": 100 * ap.mean(), "aprobados_perdidos": int(perdidos.sum()),
                      "aprobados_perdidos_pct": 100 * perdidos.sum() / base.sum(),
                      "monto_perdido_pct": 100 * df.loc[perdidos, "monto"].sum() / df.loc[base, "monto"].sum(),
                      "spread_anual_perdido": float(ingreso_spread[perdidos].sum()),
                      **{f"impacto_{g}": v for g, v in impacto_adverso(df, ap).items()},
                      **{f"perdidos_{g}_pct": 100 * (perdidos & (df["grupo"] == g)).sum() / max((base & (df["grupo"] == g)).sum(), 1)
                         for g in [REFERENCIA, *GRUPOS]}})
    return pd.DataFrame(filas)


def rechazos_solo_dti(df: pd.DataFrame, tramo: str = "50-60") -> dict:
    """Solicitudes rechazadas sólo por deuda-ingreso en un tramo: lo máximo que agregaría relajar el tope."""
    r = df[(df["resultado"] == "rechazado") & (df["dti_tramo"] == tramo) & (df["motivo_rechazo_1"] == 1) & df["motivo_rechazo_2"].isna()]
    return {"solicitudes": len(r), "monto": float(r["monto"].sum()),
            "aprobacion_pct_si_se_aprueban": 100 * (df["aprobado"].sum() + len(r)) / len(df)}


def brecha_condicional(df: pd.DataFrame) -> pd.DataFrame:
    """Brecha de rechazo contra el grupo de referencia, en puntos, agregando controles por etapas.

    Las solicitudes sin deuda-ingreso, LTV o ingreso se mantienen con una categoría propia: son sobre todo
    rechazadas, y sacarlas sesgaría la comparación entre grupos.
    """
    m = df[df["grupo"].isin([REFERENCIA, *GRUPOS])].copy()
    y = (m["resultado"] == "rechazado").astype(float)
    grupos = pd.get_dummies(m["grupo"])[GRUPOS].astype(float)
    dti = m["dti_orden"].map(lambda v: "sin_dato" if pd.isna(v) else str(int(v)))
    ingreso_ok = m["ingreso_miles"] > 0
    riesgo = pd.concat([pd.get_dummies(dti, prefix="dti", drop_first=True),
                        pd.get_dummies(m["ltv_tramo"].fillna("sin_dato"), prefix="ltv", drop_first=True)], axis=1).astype(float)
    riesgo["log_ingreso"] = np.log(m["ingreso_miles"].where(ingreso_ok)).fillna(0)
    riesgo["sin_ingreso"] = (~ingreso_ok).astype(float)
    riesgo["log_monto"] = np.log(m["monto"])
    producto = pd.concat([pd.get_dummies(m["producto"], prefix="prod", drop_first=True),
                          pd.get_dummies(m["anio"].astype(str), prefix="anio", drop_first=True)], axis=1).astype(float)
    especificaciones = {"bruta": [grupos], "con_perfil": [grupos, riesgo], "con_producto": [grupos, riesgo, producto],
                        "con_prestamista": [grupos, riesgo, producto]}
    filas = []
    for nombre, bloques in especificaciones.items():
        X = pd.concat(bloques, axis=1)
        Y = y
        if nombre == "con_prestamista":  # efectos fijos: resta la media de cada prestamista
            X = X - X.groupby(m["prestamista_lei"]).transform("mean")
            Y = y - y.groupby(m["prestamista_lei"]).transform("mean")
        else:
            X = sm.add_constant(X)
        r = sm.OLS(Y.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(m["prestamista_lei"])[0]})
        col = list(X.columns)
        for g in GRUPOS:
            i = col.index(g)
            filas.append({"especificacion": nombre, "grupo": g, "brecha_pp": 100 * r.params[i], "error_pp": 100 * r.bse[i],
                          "ic_inf_pp": 100 * (r.params[i] - 1.96 * r.bse[i]), "ic_sup_pp": 100 * (r.params[i] + 1.96 * r.bse[i]),
                          "n": len(m)})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- Bondora

def creditos(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql("""select o.prestamo_id, o.pais, o.rating, o.fecha_otorgamiento, o.monto_otorgado as monto, o.tasa_inicial as tasa,
                             o.carga_pct, o.evento_12m, coalesce(l.lgd_pct, a.lgd_pct) / 100 as lgd
                      from int_bondora__originacion o
                      cross join (select sum(lgd_pct * exposicion) / sum(exposicion) as lgd_pct from mart_lgd_pais) a
                      left join mart_lgd_pais l on o.pais = l.pais
                      order by o.prestamo_id""").df()  # orden fijo: el bootstrap no depende de la corrida


def margen(df: pd.DataFrame, costo_pp: float) -> pd.Series:
    """Resultado del primer año por crédito: tasa - costo sobre el monto, menos la pérdida si hubo evento.

    Usa el monto como exposición, lo que exagera un poco la pérdida porque ya se pagaron algunas cuotas.
    """
    return df["monto"] * (df["tasa"] - costo_pp / 100) - df["evento_12m"] * df["lgd"] * df["monto"]


def reglas(cfg: dict) -> dict:
    r = {"Sin cambios": lambda d: pd.Series(True, index=d.index)}
    for t in cfg["topes_carga"]:
        r[f"Carga <= {t}%"] = lambda d, t=t: d["carga_pct"] <= t
    for nombre, ratings in cfg["excluir_ratings"].items():
        r[f"Sin ratings {nombre}"] = lambda d, ratings=ratings: ~d["rating"].isin(ratings)
    paises = cfg["excluir_paises"]
    r[f"Sin {' ni '.join(paises)}"] = lambda d: ~d["pais"].isin(paises)
    return r


def simular_reglas(df: pd.DataFrame, cfg: dict, costo_pp: float, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    m = margen(df, costo_pp)
    filas = []
    for nombre, regla in reglas(cfg).items():
        queda = regla(df)
        sale = m[~queda].to_numpy()
        if len(sale):
            remuestras = rng.integers(0, len(sale), size=(cfg["bootstrap"], len(sale)))
            ic = np.percentile(-sale[remuestras].sum(axis=1), [2.5, 97.5])
        else:
            ic = [0.0, 0.0]
        filas.append({"regla": nombre, "costo_pp": costo_pp, "aprobados_pct": 100 * queda.mean(),
                      "monto_pct": 100 * df.loc[queda, "monto"].sum() / df["monto"].sum(),
                      "evento_12m_pct": 100 * df.loc[queda, "evento_12m"].mean(),
                      "margen_pct_monto": 100 * m[queda].sum() / df.loc[queda, "monto"].sum(),
                      "cambio_resultado": float(-sale.sum()), "cambio_ic_inf": float(ic[0]), "cambio_ic_sup": float(ic[1])})
    return pd.DataFrame(filas)


def segmentos_politica(df: pd.DataFrame) -> pd.DataFrame:
    """Créditos agregados por año, país, rating y carga: lo que necesita el simulador de Excel para repetir las reglas."""
    d = df.assign(anio=pd.to_datetime(df["fecha_otorgamiento"]).dt.year,
                  carga_orden=pd.cut(df["carga_pct"], [-np.inf, 10, 15, 20, np.inf], labels=[1, 2, 3, 4]).astype(int),
                  interes=df["monto"] * df["tasa"], monto_evento=df["monto"] * df["evento_12m"])
    d["carga"] = d["carga_orden"].map({1: "<=10", 2: "10-15", 3: "15-20", 4: ">20"})
    return (d.groupby(["anio", "pais", "rating", "carga", "carga_orden"], as_index=False)
            .agg(creditos=("monto", "size"), monto=("monto", "sum"), interes=("interes", "sum"),
                 eventos=("evento_12m", "sum"), monto_evento=("monto_evento", "sum")))


def estabilidad(df: pd.DataFrame, cfg: dict, costo_pp: float) -> pd.DataFrame:
    """Margen sobre monto de lo que cada regla deja afuera, por semestre: ¿pierde siempre o fue un período?"""
    m = margen(df, costo_pp)
    sem = df["fecha_otorgamiento"].pipe(pd.to_datetime).dt.to_period("Q").map(lambda p: f"{p.year}-S{(p.quarter + 1) // 2}")
    filas = []
    for nombre, regla in reglas(cfg).items():
        fuera = ~regla(df)
        if fuera.any():
            g = pd.DataFrame({"m": m[fuera], "monto": df.loc[fuera, "monto"], "sem": sem[fuera]}).groupby("sem").sum()
            filas += [{"regla": nombre, "semestre": s, "margen_pct_monto": 100 * f["m"] / f["monto"]} for s, f in g.iterrows()]
    return pd.DataFrame(filas)


def redondear(x):
    """Sin ruido de punto flotante entre máquinas: el commit mensual sólo muestra cambios reales."""
    if isinstance(x, dict):
        return {k: redondear(v) for k, v in x.items()}
    if isinstance(x, list):
        return [redondear(v) for v in x]
    return round(x, 4) if isinstance(x, float) else x


def main() -> None:
    cfg = settings()["politica"]
    con = duckdb.connect(str(path("warehouse") / "ciclo.duckdb"), read_only=True)
    h = solicitudes(con)
    conv = h[h["producto"] == "Conventional"]
    topes = simular_topes(conv, [*cfg["topes_dti"], SIN_TOPE])
    relajar = rechazos_solo_dti(conv)
    brechas = brecha_condicional(h)
    impacto_actual = impacto_adverso(h, h["aprobado"])

    b = creditos(con)
    sim = pd.concat([simular_reglas(b, cfg, c) for c in cfg["costos_pp"]], ignore_index=True)
    est = estabilidad(b, cfg, cfg["costos_pp"][-1])

    out = path("outputs") / "originacion"
    out.mkdir(parents=True, exist_ok=True)
    topes.to_csv(out / "simulacion_tope_dti.csv", index=False, float_format="%.4f")
    brechas.to_csv(out / "brecha_condicional.csv", index=False, float_format="%.4f")
    sim.to_csv(out / "simulacion_reglas_bondora.csv", index=False, float_format="%.4f")
    est.to_csv(out / "estabilidad_reglas.csv", index=False, float_format="%.4f")
    segmentos_politica(b).to_csv(out / "segmentos_politica.csv", index=False, float_format="%.4f")
    b.groupby("pais", as_index=False)["lgd"].first().to_csv(out / "segmentos_politica_lgd.csv", index=False, float_format="%.6f")
    resumen = {
        "solicitudes_con_decision": len(h), "convencionales": len(conv), "creditos_bondora": len(b),
        "aprobacion_convencional_pct": 100 * float(conv["aprobado"].mean()),
        "impacto_adverso_actual": impacto_actual, "relajar_tope_convencional": relajar,
        "umbral_impacto_adverso": cfg["umbral_impacto_adverso"],
    }
    with open(out / "resumen_originacion.json", "w", encoding="utf-8") as fh:
        json.dump(redondear(resumen), fh, ensure_ascii=False, indent=2)
    print(f"originacion: {out}")


if __name__ == "__main__":
    main()
