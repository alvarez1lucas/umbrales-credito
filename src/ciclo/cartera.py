"""Resumen de cartera: las cifras clave que usan el sitio, el memo y los tableros.

`python -m ciclo.cartera` escribe outputs/cartera/resumen_cartera.json desde el warehouse.
"""

from __future__ import annotations

import json

import duckdb
import pandas as pd

from ciclo.config import path
from ciclo.originacion import redondear


def _df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.sql(sql).df()


def indicadores_mora(tramos: pd.DataFrame) -> dict:
    """PAR30 y PAR90 de la cartera viva, con y sin los créditos en default que siguen en balance."""
    total = tramos["saldo_capital"].sum()
    par30 = tramos.loc[tramos["tramo"].isin(["31-60", "61-90", "90+"]), "saldo_capital"].sum()
    par90 = tramos.loc[tramos["tramo"] == "90+", "saldo_capital"].sum()
    al_corriente = total - par90
    atraso_temprano = par30 - par90
    return {"saldo_total": total, "par30_pct": 100 * par30 / total, "par90_pct": 100 * par90 / total,
            "atraso_31_90_sobre_no_vencida_pct": 100 * atraso_temprano / al_corriente}


def concentracion(por_pais: pd.Series) -> dict:
    """Participación por país e índice de Herfindahl (0 a 1)."""
    p = por_pais / por_pais.sum()
    return {"hhi": float((p**2).sum()), "participacion_pct": (100 * p).round(1).sort_values(ascending=False).to_dict()}


def ecl_con_otra_lgd(previsiones: pd.DataFrame, lgd_base: float, lgd_nueva: float) -> float:
    """Pérdida esperada reescalando las etapas 1 y 2, las únicas que dependen de la LGD."""
    e12 = previsiones.loc[previsiones["etapa"] < 3, "perdida_esperada"].sum()
    e3 = previsiones.loc[previsiones["etapa"] == 3, "perdida_esperada"].sum()
    return float(e3 + e12 * lgd_nueva / lgd_base)


def main() -> None:
    con = duckdb.connect(str(path("warehouse") / "ciclo.duckdb"), read_only=True)
    ultima = "(select max(fecha_foto) from mart_cartera_tramos)"
    tramos = _df(con, f"select * from mart_cartera_tramos where fecha_foto = {ultima}")
    prev = _df(con, "select * from mart_previsiones")
    seg = _df(con, "select * from mart_perdida_segmentos order by pais, rating")
    ren = _df(con, "select * from mart_rentabilidad_cosechas")
    cos = _df(con, "select * from mart_cosechas")
    rec = _df(con, "select * from mart_recupero_observado")
    trans = _df(con, "select * from mart_roll_rates")
    res_cob = json.loads((path("outputs") / "cobranzas" / "resumen_cobranzas.json").read_text(encoding="utf-8"))

    por_situacion = prev.groupby("situacion")[["creditos", "saldo_capital", "prevision_bcra", "perdida_esperada"]].sum()
    por_pais = prev.groupby("pais")[["saldo_capital", "prevision_bcra", "perdida_esperada"]].sum()
    ecl = float(prev["perdida_esperada"].sum())
    ecl_baja = ecl_con_otra_lgd(prev, res_cob["lgd_madura_pct"], res_cob["lgd_encadenada_pct"])

    ren_anual = ren.assign(p=ren["monto"]).groupby("cosecha_anio").apply(
        lambda g: pd.Series({c: (g[c] * g["monto"]).sum() / g["monto"].sum()
                             for c in ("evento_90_pct", "capital_perdido_pct", "intereses_cobrados_pct",
                                       "comisiones_cobradas_pct", "resultado_pct")} | {"monto": g["monto"].sum()}),
        include_groups=False)

    cos["anio"] = pd.to_datetime(cos["cosecha"]).dt.year
    curvas = cos[cos["mes"].isin([12, 24, 36])].groupby(["anio", "mes"])["tasa_evento_pct"].mean().unstack().round(1)

    matriz = trans.pivot(index="tramo_desde", columns="tramo_hasta", values="pct_del_tramo").round(1)

    resumen = {
        "fecha": str(pd.to_datetime(prev["fecha_foto"].iloc[0]).date()),
        "creditos_historicos": int(con.sql("select count(*) from fct_prestamos").fetchall()[0][0]),
        "mora": indicadores_mora(tramos),
        "concentracion": concentracion(por_pais["saldo_capital"]),
        "previsiones": {
            "por_situacion": por_situacion.round(0).reset_index().to_dict("records"),
            "por_pais": por_pais.round(0).reset_index().to_dict("records"),
            "bcra_total": float(prev["prevision_bcra"].sum()), "ecl_total": ecl, "ecl_lgd_encadenada": ecl_baja,
            "saldo_total": float(prev["saldo_capital"].sum()),
        },
        "transiciones_pct": {k: {c: v for c, v in fila.items() if pd.notna(v)} for k, fila in matriz.to_dict("index").items()},
        "cosechas_pct": {str(a): {str(m): (None if pd.isna(v) else v) for m, v in f.items()} for a, f in curvas.to_dict("index").items()},
        "rentabilidad_anual": ren_anual.round(1).reset_index().to_dict("records"),
        "segmentos": seg.round(2).to_dict("records"),
        "recupero_observado": rec.groupby("antiguedad_evento")[["capital_cobrado", "saldo_inicial"]].sum()
            .assign(pct=lambda d: 100 * d["capital_cobrado"] / d["saldo_inicial"])["pct"].round(1).to_dict(),
    }
    out = path("outputs") / "cartera"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "resumen_cartera.json", "w", encoding="utf-8") as fh:
        json.dump(redondear(resumen), fh, ensure_ascii=False, indent=2, default=float)
    print(f"cartera: {out}")


if __name__ == "__main__":
    main()
