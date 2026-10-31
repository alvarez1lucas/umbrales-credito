"""Cobranzas: a quién gestionar primero y por qué canal.

`python -m ciclo.cobranzas` escribe outputs/cobranzas/.

Priorización con resultados reales. Entre dos fotos se sabe qué pasó con cada crédito atrasado (se curó,
se pagó o terminó en 90+ o castigo), así que se puede hacer un backtest: los segmentos se calibran con una
mitad de los créditos y las reglas se evalúan sobre la otra. Se mide qué parte del saldo que terminó mal
queda cubierta si el equipo sólo llega a una fracción de las cuentas.

Lo que los datos no dicen es cuánto cambia el resultado por gestionar: Bondora no publica gestiones ni
hay grupo de control. Por eso el efecto de gestionar y todo lo de canales son **supuestos** de
config/settings.yaml (`cobranzas`), rotulados como escenario y con sensibilidad.
"""

from __future__ import annotations

import hashlib
import json

import duckdb
import numpy as np
import pandas as pd

from ciclo.config import path, settings

TRAMOS = ["1-30", "31-60", "61-90"]


def pares(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Créditos atrasados en la primera foto, con su resultado en la siguiente."""
    return con.sql("""
        with fotos as (select min(fecha_foto) as desde from int_bondora__estados)
        select a.prestamo_id, a.pais, a.tramo, a.dias_atraso as dias, a.saldo_capital as saldo, a.edad_meses,
               b.tramo in ('90+', 'castigado') as termino_mal,
               b.tramo in ('al_dia', 'pagado') as se_curo
        from int_bondora__estados a
        join fotos f on a.fecha_foto = f.desde
        join int_bondora__estados b on a.prestamo_id = b.prestamo_id and b.fecha_foto > a.fecha_foto
        where a.tramo in ('1-30', '31-60', '61-90') and a.saldo_capital > 0
        qualify b.fecha_foto = min(b.fecha_foto) over (partition by a.prestamo_id)
        order by a.prestamo_id  -- orden fijo: los empates de la priorización no dependen de la corrida
    """).df()


def mitad(prestamo_id: str) -> bool:
    """Partición estable por crédito: no depende del orden de las filas ni de una semilla."""
    return int(hashlib.md5(prestamo_id.encode()).hexdigest(), 16) % 2 == 0


def segmentar(df: pd.DataFrame, cortes_saldo: list[float]) -> pd.DataFrame:
    """Segmento = tramo × grupo de saldo × país principal."""
    principales = settings()["cobranzas"]["paises_principales"]
    out = df.copy()
    out["grupo_saldo"] = pd.cut(out["saldo"], [-np.inf, *cortes_saldo, np.inf], labels=["bajo", "medio", "alto"]).astype(str)
    out["grupo_pais"] = out["pais"].where(out["pais"].isin(principales), "Otros")
    out["segmento"] = out["tramo"] + "|" + out["grupo_saldo"] + "|" + out["grupo_pais"]
    return out


def calibrar(entrenamiento: pd.DataFrame, minimo: int) -> tuple[pd.Series, pd.Series]:
    """Probabilidad de terminar mal por segmento y, para segmentos chicos, por tramo."""
    por_tramo = entrenamiento.groupby("tramo")["termino_mal"].mean()
    g = entrenamiento.groupby("segmento")["termino_mal"].agg(["mean", "size"])
    return g.loc[g["size"] >= minimo, "mean"], por_tramo


def puntuar(df: pd.DataFrame, por_segmento: pd.Series, por_tramo: pd.Series, lgd: float, efecto: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    out["prob_mal"] = out["segmento"].map(por_segmento).fillna(out["tramo"].map(por_tramo))
    out["perdida_esperada"] = out["saldo"] * out["prob_mal"] * lgd
    out["salvable"] = out["perdida_esperada"] * out["tramo"].map(efecto)
    return out


def cobertura(df: pd.DataFrame, orden: str, capacidad: float) -> float:
    """% del saldo que terminó mal que cae dentro de las cuentas gestionadas, si se ordena por `orden`."""
    n = int(round(len(df) * capacidad))
    top = df.sort_values(orden, ascending=False, kind="stable").head(n)
    return 100 * (top["saldo"] * top["termino_mal"]).sum() / (df["saldo"] * df["termino_mal"]).sum()


def perdida_evitada(df: pd.DataFrame, orden: str, capacidad: float, lgd: float, efecto: dict[str, float]) -> float:
    """Escenario: pérdida evitada si gestionar evita el evento en la proporción supuesta por tramo."""
    n = int(round(len(df) * capacidad))
    top = df.sort_values(orden, ascending=False, kind="stable").head(n)
    return float((top["saldo"] * top["termino_mal"] * lgd * top["tramo"].map(efecto)).sum())


def backtest(prueba: pd.DataFrame, capacidades: list[float], lgd: float, efecto: dict[str, float]) -> pd.DataFrame:
    filas = []
    for nombre, orden in (("mas_atrasados", "dias"), ("mayor_saldo", "saldo"),
                          ("mayor_perdida_esperada", "perdida_esperada"), ("mas_salvable", "salvable")):
        for c in capacidades:
            filas.append({"regla": nombre, "capacidad_pct": 100 * c, "saldo_malo_cubierto_pct": cobertura(prueba, orden, c),
                          "perdida_evitada_escenario": perdida_evitada(prueba, orden, c, lgd, efecto)})
    return pd.DataFrame(filas)


def exito_canal(c: dict, cfg: dict, mult_contacto: float = 1.0) -> float:
    """Proporción de la pérdida en riesgo que evita un contacto por este canal en el primer tramo."""
    return min(c["contacto"] * mult_contacto, 1) * c["promesa"] * c["cumplimiento"] * cfg["incrementalidad"]


def canales(resumen_tramo: pd.DataFrame, cfg: dict, lgd: float, mult_contacto: float = 1.0, mult_costo: float = 1.0) -> pd.DataFrame:
    """Escenario por canal y tramo: pérdida evitada por cuenta, por euro gastado y resultado neto.

    Las tasas del canal valen para el primer tramo; en los siguientes se atenúan en la misma proporción
    que `efecto_gestion`, porque un crédito más atrasado es más difícil de revertir.
    """
    filas = []
    base = cfg["efecto_gestion"]["1-30"]
    for t in resumen_tramo.itertuples():
        en_riesgo = t.saldo_medio * t.prob_mal * lgd
        atenuacion = cfg["efecto_gestion"][t.tramo] / base
        for canal, c in cfg["canales"].items():
            evitado = en_riesgo * exito_canal(c, cfg, mult_contacto) * atenuacion
            costo = c["costo"] * mult_costo
            filas.append({"tramo": t.tramo, "canal": canal, "evitado_por_cuenta": evitado, "costo_por_cuenta": costo,
                          "neto_por_cuenta": evitado - costo, "evitado_por_euro": evitado / costo})
    return pd.DataFrame(filas)


def saldo_equilibrio(resumen_tramo: pd.DataFrame, cfg: dict, lgd: float, mult_contacto: float = 1.0, mult_costo: float = 1.0) -> dict[str, float]:
    """Saldo desde el cual llamar deja más neto que escribir por WhatsApp, en cada tramo."""
    llamada, whatsapp = cfg["canales"]["llamada"], cfg["canales"]["whatsapp"]
    extra_exito = exito_canal(llamada, cfg, mult_contacto) - exito_canal(whatsapp, cfg, mult_contacto)
    extra_costo = (llamada["costo"] - whatsapp["costo"]) * mult_costo
    base = cfg["efecto_gestion"]["1-30"]
    return {t.tramo: float(extra_costo / (t.prob_mal * lgd * extra_exito * cfg["efecto_gestion"][t.tramo] / base))
            for t in resumen_tramo.itertuples()}


def lgd_encadenada(con: duckdb.DuckDBPyConnection) -> float:
    """LGD implícita en el recupero real entre fotos.

    Encadena tramos de antigüedad separados por el horizonte entre fotos (~15 meses): un crédito que arranca
    en 0-6 pasa por 12-24, 24-36 y 36+. Es una lectura aproximada, porque los tramos no calzan exactos.
    """
    t = con.sql("""select antiguedad_evento, sum(capital_cobrado) / sum(saldo_inicial) as r
                   from mart_recupero_observado group by 1""").df().set_index("antiguedad_evento")["r"]
    return float(100 * np.prod([1 - t[a] for a in ("0-6", "12-24", "24-36", "36+")]))


def main() -> None:
    cfg = settings()["cobranzas"]
    con = duckdb.connect(str(path("warehouse") / "ciclo.duckdb"), read_only=True)
    df = pares(con)
    cortes = df["saldo"].quantile([1 / 3, 2 / 3]).round(0).tolist()
    df = segmentar(df, cortes)
    df["entrenamiento"] = df["prestamo_id"].map(mitad)
    lgd = con.sql("select sum(lgd_pct * exposicion) / sum(exposicion) from mart_lgd_pais").fetchall()[0][0] / 100
    por_segmento, por_tramo = calibrar(df[df["entrenamiento"]], cfg["minimo_segmento"])
    prueba = puntuar(df[~df["entrenamiento"]], por_segmento, por_tramo, lgd, cfg["efecto_gestion"])
    bt = backtest(prueba, cfg["capacidades"], lgd, cfg["efecto_gestion"])

    resultados = df.groupby("tramo").agg(creditos=("saldo", "size"), saldo=("saldo", "sum"), saldo_medio=("saldo", "mean"),
                                         prob_mal=("termino_mal", "mean"), prob_cura=("se_curo", "mean")).reindex(TRAMOS).reset_index()
    tabla = canales(resultados, cfg, lgd)
    sensibilidad = {nombre: {k: round(v) for k, v in saldo_equilibrio(resultados, cfg, lgd, mc, mk).items()}
                    for nombre, (mc, mk) in {"base": (1, 1), "contacto_mitad": (0.5, 1), "costo_doble": (1, 2)}.items()}

    vigente = con.sql("""
        select tramo, count(*) as creditos, sum(saldo_capital) as saldo
        from int_bondora__estados
        where fecha_foto = (select max(fecha_foto) from int_bondora__estados) and tramo in ('1-30', '31-60', '61-90')
        group by 1
    """).df().set_index("tramo").reindex(TRAMOS).reset_index()

    out = path("outputs") / "cobranzas"
    out.mkdir(parents=True, exist_ok=True)
    bt.to_csv(out / "backtest_priorizacion.csv", index=False, float_format="%.4f")
    resultados.to_csv(out / "resultado_por_tramo.csv", index=False, float_format="%.4f")
    tabla.to_csv(out / "escenario_canales.csv", index=False, float_format="%.4f")
    fechas = con.sql("select min(fecha_foto), max(fecha_foto) from int_bondora__estados").fetchall()[0]
    resumen = {
        "fecha_desde": str(fechas[0]), "fecha_hasta": str(fechas[1]), "creditos_atrasados": len(df), "creditos_prueba": len(prueba),
        "cortes_saldo": cortes, "lgd_madura_pct": round(100 * lgd, 1), "lgd_encadenada_pct": round(lgd_encadenada(con), 1),
        "efecto_gestion_supuesto": cfg["efecto_gestion"], "incrementalidad_supuesta": cfg["incrementalidad"],
        "saldo_equilibrio_llamada": sensibilidad,
        "cartera_atrasada_vigente": vigente.round(2).to_dict("records"),
    }
    with open(out / "resumen_cobranzas.json", "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2)
    print(f"cobranzas: {out}")


if __name__ == "__main__":
    main()
