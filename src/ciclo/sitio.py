"""Sitio bilingüe en HTML estático, ordenado por las cinco preguntas que hay que hacerle a un umbral.

`python -m ciclo.sitio` escribe site/index.html (español) y site/en/index.html (inglés).
Ningún número está escrito a mano: todo sale de outputs/.
"""

from __future__ import annotations

import json
import shutil

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from ciclo.config import ROOT, path, settings

OUT = path("outputs")
PLOTLY_JS = "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"
PLOTLY_ES = "https://cdn.jsdelivr.net/npm/plotly.js@2.35.2/dist/plotly-locale-es.js"
SERIES = {"s1": ("#2a78d6", "#3987e5"), "s2": ("#eb6834", "#d95926"), "s3": ("#1baf7a", "#199e70")}
TINTA = {"claro": {"texto": "#0b0b0b", "secundario": "#52514e", "grilla": "#e1e0d9", "eje": "#c3c2b7"},
         "oscuro": {"texto": "#f0efec", "secundario": "#c3c2b7", "grilla": "#2c2c2a", "eje": "#383835"}}
NEUTRO = "#898781"
RATINGS = ["AA", "A", "B", "C", "D", "E", "F", "G"]
T = {"es": {"lang": "es", "dec": ",", "mil": ".", "meses": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]},
     "en": {"lang": "en", "dec": ".", "mil": ",", "meses": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}}
GRUPO = {"es": {"Negro": "Negros", "Hispano": "Hispanos", "Asiático": "Asiáticos"},
         "en": {"Negro": "Black", "Hispano": "Hispanic", "Asiático": "Asian"}}
REGLA = {"es": {"Sin Denmark ni Latvia": "Sin Dinamarca ni Letonia", "Sin ratings E-G": "Sin ratings E a G", "Sin ratings F-G": "Sin ratings F y G",
                "Carga <= 20%": "Carga de 20% o menos", "Carga <= 15%": "Carga de 15% o menos", "Carga <= 10%": "Carga de 10% o menos"},
         "en": {"Sin Denmark ni Latvia": "No Denmark or Latvia", "Sin ratings E-G": "No ratings E to G", "Sin ratings F-G": "No ratings F and G",
                "Carga <= 20%": "Payment burden 20% or less", "Carga <= 15%": "Payment burden 15% or less", "Carga <= 10%": "Payment burden 10% or less"}}


def num(x: float, lang: str, d: int = 1) -> str:
    s = f"{x:,.{d}f}"
    if T[lang]["dec"] == ",":
        s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return s


def signo(x: float, lang: str, d: int = 1) -> str:
    return ("+" if x >= 0 else "") + num(x, lang, d)


def mes(fecha, lang: str) -> str:
    f = pd.Timestamp(fecha)
    return f"{T[lang]['meses'][f.month - 1]}-{str(f.year)[2:]}"


# --------------------------------------------------------------------------- datos

def _csv(rel: str, **kw) -> pd.DataFrame:
    return pd.read_csv(OUT / rel, **kw)


def _json(rel: str) -> dict:
    with open(OUT / rel, encoding="utf-8") as fh:
        return json.load(fh)


def datos() -> dict:
    return {
        "dti": _csv("marts/mart_aprobacion_dti.csv"), "motivos": _csv("marts/mart_motivos_rechazo.csv"), "embudo": _csv("marts/mart_embudo.csv"),
        "carga": _csv("marts/mart_carga_mora.csv"), "segmentos": _csv("marts/mart_perdida_segmentos.csv"), "cosechas": _csv("marts/mart_cosechas.csv"),
        "roll": _csv("marts/mart_roll_rates.csv"), "topes": _csv("originacion/simulacion_tope_dti.csv"),
        "reglas": _csv("originacion/simulacion_reglas_bondora.csv"), "brecha": _csv("originacion/brecha_condicional.csv"),
        "estabilidad": _csv("originacion/estabilidad_reglas.csv"), "backtest": _csv("cobranzas/backtest_priorizacion.csv"),
        "tramos": _csv("cobranzas/resultado_por_tramo.csv"), "orig": _json("originacion/resumen_originacion.json"),
        "cob": _json("cobranzas/resumen_cobranzas.json"), "cartera": _json("cartera/resumen_cartera.json"),
    }


def cifras(d: dict, L: str) -> dict:
    """Números clave formateados para el idioma `L`."""
    pp = lambda x, k=1: num(x, L, k)  # noqa: E731
    conv = d["dti"][d["dti"]["producto"] == "Conventional"].set_index("dti")
    fha = d["dti"][d["dti"]["producto"] == "FHA"].set_index("dti")
    plano = conv[(conv["dti_orden"] >= 25) & (conv["dti_orden"] <= 49)]
    em = d["embudo"].groupby("resultado")["solicitudes"].sum()
    mot = d["motivos"].groupby("motivo")["rechazos"].sum()
    t = d["topes"].set_index("tope_dti")
    r = d["reglas"][d["reglas"]["costo_pp"] == d["reglas"]["costo_pp"].max()].set_index("regla")
    r0 = d["reglas"][d["reglas"]["costo_pp"] == 0].set_index("regla")
    b = d["brecha"].set_index(["especificacion", "grupo"])
    e = d["estabilidad"].set_index(["regla", "semestre"])["margen_pct_monto"]
    fg = e["Sin ratings F-G"]
    dl = e["Sin Denmark ni Latvia"]
    bt = d["backtest"][d["backtest"]["capacidad_pct"] == 20].set_index("regla")
    tr = d["tramos"].set_index("tramo")
    seg = d["segmentos"].set_index(["pais", "rating"])
    c = d["cartera"]
    sit = {s["situacion"]: s for s in c["previsiones"]["por_situacion"]}
    prev = c["previsiones"]
    cob = d["cob"]
    costo = int(r["costo_pp"].iloc[0])
    return {
        "plano": pp(100 * plano["aprobadas"].sum() / plano["decisiones"].sum(), 0), "ap50": pp(conv.loc["50-60", "aprobacion_pct"], 0),
        "ap60": pp(conv.loc[">60", "aprobacion_pct"], 0), "fha50": pp(fha.loc["50-60", "aprobacion_pct"], 0), "fha60": pp(fha.loc[">60", "aprobacion_pct"], 0),
        "n49": pp(conv.loc["49", "decisiones"], 0), "n47": pp(conv.loc["47", "decisiones"], 0), "n48": pp(conv.loc["48", "decisiones"], 0),
        "sp20": pp(conv.loc["20-30", "spread_mediano"], 2), "sp49": pp(conv.loc["47", "spread_mediano"], 2), "sp50": pp(conv.loc["50-60", "spread_mediano"], 2), "sp60": pp(conv.loc[">60", "spread_mediano"], 2),
        "otorgado": pp(100 * em["otorgado"] / em.sum(), 0), "desiste": pp(100 * (em["desistido"] + em["incompleto"]) / em.sum(), 0), "rechazado": pp(100 * em["rechazado"] / em.sum(), 0),
        "mot_dti": pp(100 * mot["Deuda sobre ingreso"] / mot.sum(), 0), "mot_hist": pp(100 * mot["Historial crediticio"] / mot.sum(), 0),
        "solicitudes": pp(em.sum(), 0), "decisiones": pp(d["orig"]["solicitudes_con_decision"], 0), "bondora_or": pp(d["orig"]["creditos_bondora"], 0),
        "ap_conv": pp(t.loc[999, "aprobacion_pct"]), "ap45": pp(t.loc[45, "aprobacion_pct"]), "ap43": pp(t.loc[43, "aprobacion_pct"]),
        "p45": pp(t.loc[45, "aprobados_perdidos_pct"], 0), "p43": pp(t.loc[43, "aprobados_perdidos_pct"], 0),
        "p45n": pp(t.loc[45, "perdidos_Negro_pct"], 0), "p45h": pp(t.loc[45, "perdidos_Hispano_pct"], 0), "p45b": pp(t.loc[45, "perdidos_Blanco_pct"], 0),
        "ai_n": pp(t.loc[999, "impacto_Negro"], 2), "ai_h": pp(t.loc[999, "impacto_Hispano"], 2), "ai45n": pp(t.loc[45, "impacto_Negro"], 2), "ai45h": pp(t.loc[45, "impacto_Hispano"], 2),
        "ai43n": pp(t.loc[43, "impacto_Negro"], 2), "ai43h": pp(t.loc[43, "impacto_Hispano"], 2), "umbral": pp(d["orig"]["umbral_impacto_adverso"], 2),
        "br_n": pp(b.loc[("bruta", "Negro"), "brecha_pp"]), "br_h": pp(b.loc[("bruta", "Hispano"), "brecha_pp"]), "br_a": signo(b.loc[("bruta", "Asiático"), "brecha_pp"], L),
        "co_n": pp(b.loc[("con_prestamista", "Negro"), "brecha_pp"]), "co_h": pp(b.loc[("con_prestamista", "Hispano"), "brecha_pp"]), "co_a": signo(b.loc[("con_prestamista", "Asiático"), "brecha_pp"], L),
        "co_n_i": pp(b.loc[("con_prestamista", "Negro"), "ic_inf_pp"]), "co_n_s": pp(b.loc[("con_prestamista", "Negro"), "ic_sup_pp"]),
        "co_h_i": pp(b.loc[("con_prestamista", "Hispano"), "ic_inf_pp"]), "co_h_s": pp(b.loc[("con_prestamista", "Hispano"), "ic_sup_pp"]),
        "rel_n": pp(d["orig"]["relajar_tope_convencional"]["solicitudes"], 0),
        "rel_pp": pp(d["orig"]["relajar_tope_convencional"]["aprobacion_pct_si_se_aprueban"] - d["orig"]["aprobacion_convencional_pct"], 0),
        "costo": str(costo), "dl": signo(r.loc["Sin Denmark ni Latvia", "cambio_resultado"] / 1e6, L, 2), "dl_i": signo(r.loc["Sin Denmark ni Latvia", "cambio_ic_inf"] / 1e6, L, 2),
        "dl_s": signo(r.loc["Sin Denmark ni Latvia", "cambio_ic_sup"] / 1e6, L, 2), "dl_sale": pp(100 - r.loc["Sin Denmark ni Latvia", "aprobados_pct"], 0),
        "eg": signo(r.loc["Sin ratings E-G", "cambio_resultado"] / 1e6, L, 2), "eg_sale": pp(100 - r.loc["Sin ratings E-G", "aprobados_pct"], 0),
        "c10": signo(r.loc["Carga <= 10%", "cambio_resultado"] / 1e6, L, 2), "todas_pierden_sin_costo": bool((r0.drop("Sin cambios")["cambio_resultado"] < 0).all()),
        "fg_ini": signo(fg.iloc[0], L), "fg_fin": signo(fg.iloc[-1], L), "dl_max": signo(dl.max(), L), "dl_min": signo(dl.min(), L),
        "cob_atr": pp(bt.loc["mas_atrasados", "saldo_malo_cubierto_pct"], 0), "cob_pe": pp(bt.loc["mayor_perdida_esperada", "saldo_malo_cubierto_pct"], 0),
        "cob_saldo": pp(bt.loc["mayor_saldo", "saldo_malo_cubierto_pct"], 0),
        "mal1": pp(100 * tr.loc["1-30", "prob_mal"], 0), "mal2": pp(100 * tr.loc["31-60", "prob_mal"], 0), "mal3": pp(100 * tr.loc["61-90", "prob_mal"], 0),
        "cura1": pp(100 * tr.loc["1-30", "prob_cura"], 0), "cura2": pp(100 * tr.loc["31-60", "prob_cura"], 0), "cura3": pp(100 * tr.loc["61-90", "prob_cura"], 0),
        "fi_aa": pp(seg.loc[("Finland", "AA"), "margen_ajustado_pct"]), "fi_f": pp(seg.loc[("Finland", "F"), "margen_ajustado_pct"]),
        "fi_t": pp(seg.loc[("Finland", "AA"), "tasa_media_pct"], 0), "fi_pd_aa": pp(seg.loc[("Finland", "AA"), "pd_12m_pct"]), "fi_pd_f": pp(seg.loc[("Finland", "F"), "pd_12m_pct"]),
        "es_t_aa": pp(seg.loc[("Estonia", "AA"), "tasa_media_pct"]), "es_t_g": pp(seg.loc[("Estonia", "G"), "tasa_media_pct"]),
        "es_m_min": pp(seg.loc["Estonia", "margen_ajustado_pct"].min(), 0), "es_m_max": pp(seg.loc["Estonia", "margen_ajustado_pct"].max(), 0),
        "carga_min": pp(d["carga"].sort_values("orden")["evento_12m_pct"].iloc[0]), "carga_max": pp(d["carga"].sort_values("orden")["evento_12m_pct"].iloc[-1]),
        "fecha": mes(c["fecha"], L), "fecha_ini": mes(cob["fecha_desde"], L), "bcra": pp(prev["bcra_total"] / 1e6, 0), "ecl": pp(prev["ecl_total"] / 1e6, 0), "ecl_b": pp(prev["ecl_lgd_encadenada"] / 1e6, 0),
        "s1_e": pp(100 * sit[1]["perdida_esperada"] / sit[1]["saldo_capital"]), "s5_e": pp(100 * sit[5]["perdida_esperada"] / sit[5]["saldo_capital"], 0),
        "lgd": pp(cob["lgd_madura_pct"], 0), "lgd_b": pp(cob["lgd_encadenada_pct"], 0), "saldo": pp(prev["saldo_total"] / 1e6, 0), "creditos": pp(c["creditos_historicos"], 0),
        "eq1": pp(cob["saldo_equilibrio_llamada"]["base"]["1-30"], 0), "eq3": pp(cob["saldo_equilibrio_llamada"]["base"]["61-90"], 0),
        "mora_url": "https://alvarez1lucas.github.io/mora_argentina/",
    }


# --------------------------------------------------------------------------- gráficos

def _layout(fig: go.Figure, lang: str, y_titulo: str, alto: int = 340, x_titulo: str = "") -> go.Figure:
    t = TINTA["claro"]
    fig.update_layout(
        height=alto, margin=dict(l=56, r=16, t=16, b=64), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=t["texto"]),
        hovermode="x unified", legend=dict(orientation="h", y=-0.24, x=0, font=dict(color=t["secundario"])),
        separators=T[lang]["dec"] + T[lang]["mil"], bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, linecolor=t["eje"], tickcolor=t["eje"], tickfont=dict(color=t["secundario"]),
                     title=dict(text=x_titulo, font=dict(color=t["secundario"], size=12)))
    fig.update_yaxes(gridcolor=t["grilla"], zeroline=False, linecolor=t["eje"], tickfont=dict(color=t["secundario"]),
                     title=dict(text=y_titulo, font=dict(color=t["secundario"], size=12)))
    return fig


def _linea(x, y, nombre: str, rol: str, fmt: str = ".1f", **kw) -> go.Scatter:
    kw.setdefault("mode", "lines+markers")
    return go.Scatter(x=x, y=y, name=nombre, line=dict(color=SERIES[rol][0], width=2), marker=dict(color=SERIES[rol][0], size=7),
                      meta={"rol": rol}, hovertemplate=f"%{{y:{fmt}}}", **kw)


def _barra(x, y, nombre: str, rol: str, fmt: str = ".1f", **kw) -> go.Bar:
    return go.Bar(x=x, y=y, name=nombre, marker=dict(color=SERIES[rol][0], cornerradius=4), meta={"rol": rol}, hovertemplate=f"%{{y:{fmt}}}", **kw)


def _ref(fig: go.Figure, y: float, texto: str, lugar: str) -> None:
    """Línea horizontal de referencia con su rótulo, en el lado donde no pisa ninguna serie."""
    fig.add_hline(y=y, line=dict(color=NEUTRO, width=1, dash="dot"), annotation_text=texto, annotation_position=lugar,
                  annotation_font=dict(color=NEUTRO, size=12))


def _tx(L: str, es: str, en: str) -> str:
    return es if L == "es" else en


def _orden_dti(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["dti"] != "sin_dato"].sort_values("dti_orden")


def fig_aprobacion(d: dict, L: str) -> go.Figure:
    t = d["dti"]
    fig = go.Figure()
    for prod, nombre, rol in (("Conventional", _tx(L, "Convencional", "Conventional"), "s1"), ("FHA", _tx(L, "FHA (garantía pública)", "FHA (government-backed)"), "s2")):
        g = _orden_dti(t[t["producto"] == prod])
        fig.add_trace(_linea(g["dti"], g["aprobacion_pct"], nombre, rol))
    _layout(fig, L, _tx(L, "Aprobación (%)", "Approval (%)"), x_titulo=_tx(L, "Deuda sobre ingreso (%)", "Debt-to-income (%)"))
    fig.update_yaxes(rangemode="tozero")
    return fig


def fig_acumulacion(d: dict, L: str) -> go.Figure:
    t = d["dti"]
    g = t[(t["producto"] == "Conventional") & t["dti"].str.fullmatch(r"\d+")].sort_values("dti_orden")
    resto, pico = g[g["dti"] != "49"], g[g["dti"] == "49"]
    fig = go.Figure([_barra(resto["dti"], resto["decisiones"], _tx(L, "Solicitudes", "Applications"), "s1", ",.0f"),
                     _barra(pico["dti"], pico["decisiones"], _tx(L, "Justo debajo del límite", "Right below the limit"), "s2", ",.0f")])
    _layout(fig, L, _tx(L, "Solicitudes con decisión", "Decided applications"), alto=300, x_titulo=_tx(L, "Deuda sobre ingreso (%)", "Debt-to-income (%)"))
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=list(g["dti"]))
    return fig


def fig_spread(d: dict, L: str) -> go.Figure:
    g = _orden_dti(d["dti"][d["dti"]["producto"] == "Conventional"])
    fig = go.Figure([_linea(g["dti"], g["spread_mediano"], _tx(L, "Spread mediano", "Median spread"), "s1", ".2f")])
    fig.update_layout(showlegend=False)
    return _layout(fig, L, _tx(L, "Puntos sobre la tasa de referencia", "Points over the benchmark"), alto=300,
                   x_titulo=_tx(L, "Deuda sobre ingreso (%)", "Debt-to-income (%)"))


def fig_margen(d: dict, L: str) -> go.Figure:
    s = d["segmentos"]
    fig = go.Figure()
    for pais, nombre, rol in (("Estonia", "Estonia", "s1"), ("Finland", _tx(L, "Finlandia", "Finland"), "s2")):
        g = s[s["pais"] == pais].set_index("rating").reindex(RATINGS).dropna(subset=["margen_ajustado_pct"])
        fig.add_trace(_linea(g.index, g["margen_ajustado_pct"], nombre, rol))
    _layout(fig, L, _tx(L, "Margen ajustado por riesgo (pp)", "Risk-adjusted margin (pp)"), alto=300, x_titulo="Rating")
    fig.update_yaxes(rangemode="tozero")
    return fig


def fig_transicion(d: dict, L: str) -> go.Figure:
    r = d["roll"]
    r = r[r["fecha_desde"] == r["fecha_desde"].min()]
    grupos = {"cura": (["al_dia", "pagado"], _tx(L, "Se curó o pagó", "Cured or repaid"), "s3"),
              "sigue": (["1-30", "31-60", "61-90"], _tx(L, "Sigue con atraso temprano", "Still in early arrears"), "s1"),
              "mal": (["90+", "castigado"], _tx(L, "90+ o castigo", "90+ or written off"), "s2")}
    tramos = ["1-30", "31-60", "61-90"]
    fig = go.Figure()
    for destinos, nombre, rol in grupos.values():
        y = [r[(r["tramo_desde"] == t) & r["tramo_hasta"].isin(destinos)]["pct_del_tramo"].sum() for t in tramos]
        fig.add_trace(_barra([f"{t} {_tx(L, 'días', 'days')}" for t in tramos], y, nombre, rol, ".0f"))
    _layout(fig, L, _tx(L, "% de los créditos del tramo", "% of loans in the bucket"), alto=320)
    fig.update_layout(barmode="stack")
    return fig


def fig_carga(d: dict, L: str) -> go.Figure:
    g = d["carga"].sort_values("orden")
    fig = go.Figure([_barra(g["carga_tramo"], g["evento_12m_pct"], _tx(L, "Mora a 12 meses", "12-month delinquency"), "s1", customdata=g["creditos"],
                            ) .update(hovertemplate=_tx(L, "%{y:.1f}% (%{customdata:,} créditos)", "%{y:.1f}% (%{customdata:,} loans)"))])
    fig.update_layout(showlegend=False)
    return _layout(fig, L, _tx(L, "Mora 90+ a 12 meses (%)", "90+ delinquency at 12 months (%)"), alto=290,
                   x_titulo=_tx(L, "Cuota sobre ingreso (%)", "Payment-to-income (%)"))


def fig_topes(d: dict, L: str) -> go.Figure:
    t = d["topes"][d["topes"]["tope_dti"] < 999].sort_values("tope_dti")
    fig = go.Figure([_linea(t["tope_dti"].astype(int).astype(str), t["aprobados_perdidos_pct"], _tx(L, "Aprobados perdidos", "Approvals lost"), "s1", ".0f")])
    fig.update_layout(showlegend=False)
    return _layout(fig, L, _tx(L, "% de los aprobados actuales", "% of current approvals"), alto=290, x_titulo=_tx(L, "Tope de deuda sobre ingreso (%)", "Debt-to-income cap (%)"))


def fig_reglas(d: dict, L: str) -> go.Figure:
    r = d["reglas"]
    r = r[(r["costo_pp"] == r["costo_pp"].max()) & (r["regla"] != "Sin cambios")].sort_values("cambio_resultado")
    x = r["cambio_resultado"] / 1e6
    fig = go.Figure(go.Bar(
        y=[REGLA[L][k] for k in r["regla"]], x=x, orientation="h", marker=dict(color=SERIES["s1"][0], cornerradius=4), meta={"rol": "s1"},
        error_x=dict(type="data", symmetric=False, array=r["cambio_ic_sup"] / 1e6 - x, arrayminus=x - r["cambio_ic_inf"] / 1e6, color=NEUTRO, thickness=1.5, width=4),
        hovertemplate="%{x:+.2f} M€<extra></extra>"))
    _layout(fig, L, "", alto=320, x_titulo=_tx(L, "Cambio en el resultado del primer año (M€)", "Change in first-year result (€M)"))
    fig.update_layout(hovermode="closest", margin=dict(l=8, b=56), showlegend=False)
    fig.update_xaxes(showgrid=True, gridcolor=TINTA["claro"]["grilla"], zeroline=True, zerolinecolor=NEUTRO)
    fig.update_yaxes(automargin=True, gridcolor="rgba(0,0,0,0)")
    return fig


def fig_cobertura(d: dict, L: str) -> go.Figure:
    b = d["backtest"]
    fig = go.Figure()
    for regla, nombre, rol in (("mayor_perdida_esperada", _tx(L, "Mayor pérdida esperada", "Highest expected loss"), "s1"),
                               ("mayor_saldo", _tx(L, "Mayor saldo", "Largest balance"), "s3"),
                               ("mas_atrasados", _tx(L, "Más atrasados", "Most days past due"), "s2")):
        g = b[b["regla"] == regla]
        fig.add_trace(_linea(g["capacidad_pct"].astype(int).astype(str) + "%", g["saldo_malo_cubierto_pct"], nombre, rol, ".0f"))
    _layout(fig, L, _tx(L, "% del saldo que terminó mal", "% of balance that went bad"), alto=320, x_titulo=_tx(L, "Cuentas que llega a gestionar el equipo", "Accounts the team can reach"))
    fig.update_yaxes(rangemode="tozero")
    return fig


def fig_impacto(d: dict, L: str) -> go.Figure:
    t = d["topes"][d["topes"]["tope_dti"] >= 40].sort_values("tope_dti")
    x = [str(int(v)) if v < 999 else _tx(L, "Actual", "Current") for v in t["tope_dti"]]
    fig = go.Figure()
    for g, rol in (("Asiático", "s3"), ("Hispano", "s2"), ("Negro", "s1")):
        fig.add_trace(_linea(x, t[f"impacto_{g}"], GRUPO[L][g], rol, ".2f"))
    _ref(fig, d["orig"]["umbral_impacto_adverso"], _tx(L, "Umbral de atención (4/5)", "Attention threshold (4/5)"), "top right")
    _layout(fig, L, _tx(L, "Aprobación relativa a blancos no hispanos", "Approval relative to non-Hispanic White"), x_titulo=_tx(L, "Tope de deuda sobre ingreso (%)", "Debt-to-income cap (%)"))
    fig.update_layout(margin=dict(b=88), legend=dict(y=-0.32))
    fig.update_xaxes(tickangle=0)
    return fig


def fig_brecha(d: dict, L: str) -> go.Figure:
    b = d["brecha"]
    fig = go.Figure()
    for esp, nombre, rol in (("bruta", _tx(L, "Bruta", "Raw"), "s2"), ("con_prestamista", _tx(L, "Con perfil, producto y prestamista", "With profile, product and lender"), "s1")):
        g = b[b["especificacion"] == esp].set_index("grupo").loc[["Negro", "Hispano", "Asiático"]]
        fig.add_trace(go.Bar(x=[GRUPO[L][k] for k in g.index], y=g["brecha_pp"], name=nombre, marker=dict(color=SERIES[rol][0], cornerradius=4), meta={"rol": rol},
                             error_y=dict(type="data", symmetric=False, array=g["ic_sup_pp"] - g["brecha_pp"], arrayminus=g["brecha_pp"] - g["ic_inf_pp"], color=NEUTRO, thickness=1.5, width=4),
                             hovertemplate="%{y:+.1f} pp"))
    _layout(fig, L, _tx(L, "Brecha de rechazo contra blancos (pp)", "Denial gap vs White (pp)"))
    fig.update_layout(barmode="group", bargroupgap=0.08)
    fig.add_hline(y=0, line=dict(color=NEUTRO, width=1))
    return fig


def fig_cosechas(d: dict, L: str) -> go.Figure:
    c = d["cosechas"].copy()
    c["anio"] = pd.to_datetime(c["cosecha"]).dt.year
    fig = go.Figure()
    for anio, rol in ((2019, "s2"), (2022, "s1"), (2024, "s3")):
        g = c[c["anio"] == anio].groupby("mes").agg(eventos=("creditos_con_evento", "sum"), n=("creditos", "sum"), q=("cosecha", "nunique"))
        g = g[g["q"] == 4]  # sólo meses que ya alcanzaron los cuatro trimestres del año: la curva no cambia de composición
        fig.add_trace(_linea(g.index, 100 * g["eventos"] / g["n"], str(anio), rol, mode="lines"))
    return _layout(fig, L, _tx(L, "Créditos con mora 90+ (%)", "Loans 90+ days past due (%)"), x_titulo=_tx(L, "Meses desde el otorgamiento", "Months since origination"))


def fig_estabilidad(d: dict, L: str) -> go.Figure:
    e = d["estabilidad"]
    fig = go.Figure()
    for regla, nombre, rol in (("Sin ratings F-G", _tx(L, "Ratings F y G", "Ratings F and G"), "s2"), ("Sin Denmark ni Latvia", _tx(L, "Dinamarca y Letonia", "Denmark and Latvia"), "s1")):
        g = e[e["regla"] == regla]
        fig.add_trace(_linea(g["semestre"], g["margen_pct_monto"], nombre, rol))
    _ref(fig, 0, _tx(L, "Punto de equilibrio", "Break-even"), "bottom left")
    return _layout(fig, L, _tx(L, "Resultado del primer año (% del monto)", "First-year result (% of amount)"), alto=310,
                   x_titulo=_tx(L, "Semestre de originación", "Origination half-year"))


def fig_previsiones(d: dict, L: str) -> go.Figure:
    s = d["cartera"]["previsiones"]["por_situacion"]
    x = [str(f["situacion"]) for f in s]
    fig = go.Figure([_barra(x, [100 * f["prevision_bcra"] / f["saldo_capital"] for f in s], _tx(L, "Previsión mínima del BCRA", "BCRA minimum provision"), "s2", ".1f"),
                     _barra(x, [100 * f["perdida_esperada"] / f["saldo_capital"] for f in s], _tx(L, "Pérdida esperada (estilo NIIF 9)", "Expected loss (IFRS 9 style)"), "s1", ".1f")])
    _layout(fig, L, _tx(L, "% del saldo", "% of balance"), x_titulo=_tx(L, "Situación del deudor", "Debtor classification"))
    fig.update_layout(barmode="group", bargroupgap=0.08)
    return fig


def _div(fig: go.Figure, id_: str, L: str) -> str:
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=id_, config={"displayModeBar": False, "responsive": True, "locale": L})


def _tile(valor: str, etiqueta: str, nota: str = "") -> str:
    n = f'<div class="tile-nota">{nota}</div>' if nota else ""
    return f'<div class="tile"><div class="tile-valor">{valor}</div><div class="tile-etq">{etiqueta}</div>{n}</div>'


def _tabla(encabezado: list[str], filas: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in encabezado)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas)
    return f'<div class="tabla"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def _etapa(L: str, clave: str) -> str:
    n = {"or": ("Originación", "Origination"), "ca": ("Cartera", "Portfolio"), "co": ("Cobranzas", "Collections")}[clave]
    return f'<span class="etapa">{n[0 if L == "es" else 1]}</span>'


def tabla_topes(d: dict, L: str) -> str:
    pp = lambda x, k=1: num(x, L, k)  # noqa: E731
    t = d["topes"].sort_values("tope_dti", ascending=False)
    t = t[t["tope_dti"].isin([999, 49, 47, 45, 43, 40])]
    filas = [[_tx(L, "Sin tope nuevo", "No new cap") if f.tope_dti == 999 else str(int(f.tope_dti)), f"{pp(f.aprobacion_pct)}%", f"{pp(f.aprobados_perdidos_pct)}%",
              f"{pp(f.monto_perdido_pct)}%", pp(f.impacto_Negro, 2), pp(f.impacto_Hispano, 2)] for f in t.itertuples()]
    return _tabla([_tx(L, "Tope", "Cap"), _tx(L, "Aprobación", "Approval"), _tx(L, "Aprobados perdidos", "Approvals lost"), _tx(L, "Monto perdido", "Volume lost"),
                   _tx(L, "Impacto adverso, negros", "Adverse impact, Black"), _tx(L, "Impacto adverso, hispanos", "Adverse impact, Hispanic")], filas)


def contenido(d: dict, L: str) -> tuple[str, str, str]:
    c = cifras(d, L)
    e = lambda k: _etapa(L, k)  # noqa: E731
    if L == "es":
        hero = "".join([
            _tile(f"{c['plano']}% → {c['ap50']}%", "Aprobación al cruzar deuda-ingreso de 50", "Créditos convencionales: la regla que nadie publica"),
            _tile(f"{c['p45']}%", "De los aprobados se pierde con un tope de 45", f"Con 43, el {c['p43']}%"),
            _tile(f"{c['ai_n']} → {c['ai45n']}", "Impacto adverso con ese tope", f"Umbral de atención: {c['umbral']}"),
            _tile(f"{c['mal1']}% → {c['mal3']}%", "Terminan mal, de 1-30 a 61-90 días", "A los 60 días la cobranza ya llegó tarde"),
        ])
        sintesis = f"""<section class="sintesis"><h2>En síntesis</h2>
<p>Una política de crédito es un conjunto de umbrales: hasta qué deuda aprobar, a qué rating prestar, a qué día de atraso llamar. Entender un umbral es poder responder cinco preguntas.</p>
<ol>
<li><strong>¿Dónde está la regla?</strong> Se ve en los datos aunque nadie la haya escrito: la aprobación cae de {c['plano']}% a {c['ap50']}% al cruzar deuda-ingreso de 50, y las solicitudes se amontonan justo debajo.</li>
<li><strong>¿La variable separa riesgo?</strong> No siempre. Por debajo de 50 la deuda-ingreso casi no mueve ni la aprobación ni el precio. En cambio, el tramo de atraso separa mucho: terminan mal el {c['mal1']}% en 1-30 días y el {c['mal3']}% en 61-90.</li>
<li><strong>¿Cuánto cuesta moverla?</strong> Bajar el tope a 45 pierde el {c['p45']}% de los aprobados. Con un costo supuesto de {c['costo']} puntos, salir de dos países que pierden siempre rinde lo mismo que recortar tres ratings, resignando un tercio de los créditos.</li>
<li><strong>¿A quién afecta?</strong> No a todos por igual. Con ese tope sale el {c['p45n']}% de los aprobados negros contra {c['p45b']}% de los blancos, y el impacto adverso baja de {c['ai_n']} a {c['ai45n']}.</li>
<li><strong>¿Sigue valiendo?</strong> Las reglas envejecen. Los ratings F y G pasaron de {c['fg_ini']}% a {c['fg_fin']}% del monto en dos años: una regla calibrada con las cosechas viejas no los habría sacado.</li>
</ol></section>"""
        secciones = f"""
<section><h2>Por qué estos datos</h2>
<p>En Argentina no hay datos públicos de créditos individuales para analizar en conjunto, así que el método se practica sobre carteras reales de otros mercados. <strong>Lo que se traslada es el razonamiento, no los números:</strong> con la cartera de cualquier empresa se recalibra todo. Cada dato cubre lo que al otro le falta.</p>
<ul>
<li><strong>HMDA (hipotecas en Georgia, EE.UU., 2023-2025):</strong> {c['solicitudes']} solicitudes con su resultado y el motivo del rechazo. Muestra a los rechazados, pero no qué pasó después con los créditos.</li>
<li><strong>Bondora (préstamos de consumo en Europa):</strong> {c['creditos']} créditos reales y dos fotos de toda la cartera, de {c['fecha_ini']} y {c['fecha']}. Muestra el resultado real, pero sólo de los otorgados.</li>
</ul></section>

<section><h2>1. ¿Dónde está la regla?</h2>
<p>{e('or')} Las solicitudes convencionales se aprueban en ~{c['plano']}% sea cual sea la deuda-ingreso, hasta que cruzan 50: ahí cae a {c['ap50']}%, y a {c['ap60']}% arriba de 60. En FHA, con garantía pública, sigue en {c['fha50']}% hasta 60 y recién ahí cae a {c['fha60']}%. <strong>El mismo cliente enfrenta otra regla según el producto.</strong></p>
{_div(fig_aprobacion(d, L), 'g-aprobacion', L)}
<p>Otra huella del límite: las solicitudes se amontonan justo debajo. Con 49 hay {c['n49']} y con 47, {c['n47']}. Cuando una distribución tiene un salto así, hay una regla, y conviene preguntarse si el dato se está ajustando para pasarla.</p>
{_div(fig_acumulacion(d, L), 'g-acumulacion', L)}
<p>De cada 100 solicitudes, {c['otorgado']} se otorgan, {c['rechazado']} se rechazan y {c['desiste']} se caen sin decisión. Entre los rechazos, deuda-ingreso ({c['mot_dti']}%) e historial crediticio ({c['mot_hist']}%) explican casi dos tercios.</p>
</section>

<section><h2>2. ¿La variable separa riesgo?</h2>
<p>{e('or')} Una regla sólo se justifica si su variable distingue buenos de malos. Por debajo de 50, la deuda-ingreso casi no mueve el precio: el spread va de {c['sp20']} a {c['sp49']} puntos. Por encima salta a {c['sp50']} y {c['sp60']}. El mercado cobra el riesgo justo donde está la regla, no de forma pareja.</p>
{_div(fig_spread(d, L), 'g-spread', L)}
<p>{e('ca')} El precio también tiene que seguir al riesgo, y eso no pasa solo. En Estonia la tasa sube con el rating ({c['es_t_aa']}% a {c['es_t_g']}%) y el margen queda plano en {c['es_m_min']}-{c['es_m_max']} puntos. En Finlandia queda en ~{c['fi_t']}% para todos, aunque la PD va de {c['fi_pd_aa']}% a {c['fi_pd_f']}%: el margen cae de {c['fi_aa']} a {c['fi_f']} puntos. Cuando la tasa no se puede mover, el único umbral disponible es a quién prestarle.</p>
{_div(fig_margen(d, L), 'g-margen', L)}
<p>{e('co')} El día de atraso es una variable que separa mucho. Quince meses después, de los créditos que estaban en 1-30 días terminó mal el {c['mal1']}%; de los de 31-60, el {c['mal2']}%; de los de 61-90, el {c['mal3']}%. La cura cae de {c['cura1']}% a {c['cura2']}% y {c['cura3']}%. <strong>La ventana útil de cobranza se cierra cerca de los 60 días.</strong></p>
{_div(fig_transicion(d, L), 'g-transicion', L)}
</section>

<section><h2>3. ¿Cuánto cuesta moverla?</h2>
<p>{e('or')} Mover un umbral es elegir qué perder. Como las solicitudes se concentran entre 36 y 49, cada punto de tope saca mucha gente: con 45 se pierde el {c['p45']}% de los aprobados, y con 43 el {c['p43']}%. Lo que HMDA no dice es cuánta mora se evita, porque no sigue a los créditos después.</p>
{tabla_topes(d, L)}
<p>{e('ca')} Bondora sí tiene el resultado real a 12 meses, y ahí las reglas se pueden valorar en euros. La mora sube con la carga de la cuota, de {c['carga_min']}% a {c['carga_max']}%, pero eso no alcanza para que un tope convenga.</p>
{_div(fig_carga(d, L), 'g-carga', L)}
<p>Con un costo supuesto de {c['costo']} puntos entre fondeo y operación, los topes de carga empeoran el resultado: recortan buenos clientes de montos altos. En cambio, sacar Dinamarca y Letonia mejora {c['dl']} M€ resignando el {c['dl_sale']}% de los créditos, y sacar E a G mejora {c['eg']} M€ resignando el {c['eg_sale']}%. <strong>Una variable puede predecir mora y aun así ser un mal umbral.</strong> Sin ese costo, ninguna regla mejora el resultado: la conclusión depende del supuesto, y hay que decirlo.</p>
{_div(fig_reglas(d, L), 'g-reglas', L)}
<p>{e('co')} En cobranza, el costo es la capacidad del equipo. Con 20% de las cuentas, gestionar a los más atrasados cubre el {c['cob_atr']}% del saldo que terminó mal; por pérdida esperada, el {c['cob_pe']}%. Casi toda la mejora viene del saldo: ordenar sólo por saldo ya llega al {c['cob_saldo']}%. La regla simple captura la mayor parte del valor.</p>
{_div(fig_cobertura(d, L), 'g-cobertura', L)}
<p class="nota">Backtest con resultados reales, calibrado en una mitad de los créditos y evaluado en la otra. Mide si la gestión llega a las cuentas que terminan mal, no si las salva: para eso hace falta un grupo de control.</p>
</section>

<section><h2>4. ¿A quién afecta?</h2>
<p>{e('or')} Un tope neutral en apariencia puede pesar distinto según el grupo. El índice de impacto adverso compara la aprobación de cada grupo con la del grupo de referencia; debajo de {c['umbral']} es una señal de atención. En convencionales, solicitantes negros ya están en {c['ai_n']}. Con tope de 45 bajan a {c['ai45n']}; con 43, a {c['ai43n']}, y los hispanos también cruzan el umbral ({c['ai43h']}).</p>
{_div(fig_impacto(d, L), 'g-impacto', L)}
<p>La brecha de rechazo se achica al comparar perfiles parecidos, pero no desaparece: para solicitantes negros baja de {c['br_n']} a {c['co_n']} puntos (IC 95%: {c['co_n_i']} a {c['co_n_s']}), y para hispanos de {c['br_h']} a {c['co_h']} ({c['co_h_i']} a {c['co_h_s']}). Para asiáticos cambia de signo, de {c['br_a']} a {c['co_a']}. <strong>Esto no prueba discriminación:</strong> HMDA público no trae el score ni el resultado del motor de decisión. Mide cuánto queda sin explicar por lo observable, que es lo que un equipo de política tiene que investigar antes de aplicar la regla.</p>
{_div(fig_brecha(d, L), 'g-brecha', L)}
</section>

<section><h2>5. ¿Sigue valiendo?</h2>
<p>{e('ca')} Un umbral se calibra con el pasado. Las cosechas muestran por qué hay que revisarlo: la de 2019 llegó a mucha más mora que las de 2022 y 2024 en la misma antigüedad.</p>
{_div(fig_cosechas(d, L), 'g-cosechas', L)}
<p>Lo mismo pasa con un segmento. Dinamarca y Letonia perdieron en todos los semestres (entre {c['dl_max']}% y {c['dl_min']}% del monto), así que esa regla es sólida. Los ratings F y G pasaron de {c['fg_ini']}% a {c['fg_fin']}%: el problema es reciente, y mirando el promedio histórico no se habría visto. <strong>Por eso un umbral necesita monitoreo, no sólo calibración.</strong></p>
{_div(fig_estabilidad(d, L), 'g-estabilidad', L)}
</section>

<section><h2>En Argentina: el umbral también lo pone la norma</h2>
<p>Las cinco preguntas valen para los umbrales regulatorios. El BCRA clasifica a los deudores de consumo por días de atraso y fija previsiones mínimas por situación. Aplicadas como ejercicio sobre esta cartera de {c['saldo']} M€, dan {c['bcra']} M€ contra {c['ecl_b']}-{c['ecl']} M€ de pérdida esperada. <strong>El total es parecido, la composición no:</strong> en situación 1, 1% contra {c['s1_e']}%, y en situación 5, 100% contra {c['s5_e']}%. La norma previsiona poco lo sano y mucho lo muy viejo, y las dos cosas se compensan.</p>
{_div(fig_previsiones(d, L), 'g-previsiones', L)}
<p>Del lado macro, el proyecto <a href="{c['mora_url']}">Mora de los hogares en Argentina</a> muestra cómo se corre el corte de aprobación cuando cambia el ciclo. Son los mismos umbrales vistos desde arriba.</p>
</section>"""
        titulo_lim = "Lo que estos datos no permiten afirmar"
        lim = [
            "HMDA no tiene score ni desempeño: los topes miden aprobación y volumen, no la mora que se evita. Son hipotecas de un solo estado.",
            "Las reglas en Bondora sólo se evalúan endureciendo, porque a los rechazados no se los observa.",
            f"El costo de {c['costo']} puntos es un supuesto y el resultado mira el primer año. Con otro costo cambia la conclusión.",
            "Dinamarca y Letonia salieron de mirar estos mismos datos: se confirman con cosechas nuevas.",
            f"Hay una sola transición de 15 meses. La LGD va de {c['lgd_b']}% a {c['lgd']}% según el método, lo que mueve la pérdida esperada de {c['ecl_b']} a {c['ecl']} M€.",
            "Bondora no publica gestiones: el efecto de gestionar y los canales son supuestos, y no se muestran como resultado.",
        ]
    else:
        hero = "".join([
            _tile(f"{c['plano']}% → {c['ap50']}%", "Approval when debt-to-income crosses 50", "Conventional loans: the rule nobody publishes"),
            _tile(f"{c['p45']}%", "Of approvals lost with a cap of 45", f"With 43, {c['p43']}%"),
            _tile(f"{c['ai_n']} → {c['ai45n']}", "Adverse impact under that cap", f"Attention threshold: {c['umbral']}"),
            _tile(f"{c['mal1']}% → {c['mal3']}%", "Go bad, from 1-30 to 61-90 days", "By day 60 collections are already late"),
        ])
        sintesis = f"""<section class="sintesis"><h2>In short</h2>
<p>A credit policy is a set of thresholds: how much debt to approve, which ratings to lend to, which day past due to call. Understanding a threshold means being able to answer five questions.</p>
<ol>
<li><strong>Where is the rule?</strong> It shows in the data even if nobody wrote it down: approval falls from {c['plano']}% to {c['ap50']}% when debt-to-income crosses 50, and applications pile up right below.</li>
<li><strong>Does the variable separate risk?</strong> Not always. Below 50, debt-to-income barely moves approval or price. Days past due, on the other hand, separate a lot: {c['mal1']}% go bad from 1-30 days and {c['mal3']}% from 61-90.</li>
<li><strong>What does moving it cost?</strong> Lowering the cap to 45 loses {c['p45']}% of approvals. With an assumed cost of {c['costo']} points, leaving two countries that always lose yields as much as cutting three ratings, giving up a third of the loans.</li>
<li><strong>Who does it affect?</strong> Not everyone equally. Under that cap {c['p45n']}% of Black approvals go, against {c['p45b']}% of White ones, and adverse impact falls from {c['ai_n']} to {c['ai45n']}.</li>
<li><strong>Does it still hold?</strong> Rules age. Ratings F and G went from {c['fg_ini']}% to {c['fg_fin']}% of the amount in two years: a rule calibrated on old vintages would not have removed them.</li>
</ol></section>"""
        secciones = f"""
<section><h2>Why these data</h2>
<p>Argentina has no public loan-level data that can be analyzed in bulk, so the method is practiced on real portfolios from other markets. <strong>What travels is the reasoning, not the numbers:</strong> everything gets recalibrated on any lender's own portfolio. Each source covers what the other lacks.</p>
<ul>
<li><strong>HMDA (mortgages in Georgia, US, 2023-2025):</strong> {c['solicitudes']} applications with their outcome and denial reason. It shows those denied, but not what happened to the loans afterwards.</li>
<li><strong>Bondora (consumer loans in Europe):</strong> {c['creditos']} real loans and two snapshots of the whole portfolio, from {c['fecha_ini']} and {c['fecha']}. It shows real outcomes, but only for loans granted.</li>
</ul></section>

<section><h2>1. Where is the rule?</h2>
<p>{e('or')} Conventional applications are approved at ~{c['plano']}% whatever the debt-to-income, until they cross 50: there it falls to {c['ap50']}%, and to {c['ap60']}% above 60. In FHA, which is government-backed, it stays at {c['fha50']}% up to 60 and only then falls to {c['fha60']}%. <strong>The same customer faces a different rule depending on the product.</strong></p>
{_div(fig_aprobacion(d, L), 'g-aprobacion', L)}
<p>Another trace of the limit: applications pile up right below it. There are {c['n49']} at 49 and {c['n47']} at 47. When a distribution jumps like that there is a rule, and it is worth asking whether the figure is being adjusted to clear it.</p>
{_div(fig_acumulacion(d, L), 'g-acumulacion', L)}
<p>Out of every 100 applications, {c['otorgado']} are granted, {c['rechazado']} denied and {c['desiste']} drop out with no decision. Among denials, debt-to-income ({c['mot_dti']}%) and credit history ({c['mot_hist']}%) explain almost two thirds.</p>
</section>

<section><h2>2. Does the variable separate risk?</h2>
<p>{e('or')} A rule is only justified if its variable tells good from bad. Below 50, debt-to-income barely moves the price: the spread goes from {c['sp20']} to {c['sp49']} points. Above it jumps to {c['sp50']} and {c['sp60']}. The market prices risk right where the rule is, not evenly.</p>
{_div(fig_spread(d, L), 'g-spread', L)}
<p>{e('ca')} Price also has to follow risk, and that does not happen by itself. In Estonia the rate rises with the rating ({c['es_t_aa']}% to {c['es_t_g']}%) and the margin stays flat at {c['es_m_min']}-{c['es_m_max']} points. In Finland it stays at ~{c['fi_t']}% for everyone, even though PD goes from {c['fi_pd_aa']}% to {c['fi_pd_f']}%: the margin falls from {c['fi_aa']} to {c['fi_f']} points. When the rate cannot move, the only threshold left is who to lend to.</p>
{_div(fig_margen(d, L), 'g-margen', L)}
<p>{e('co')} Days past due is a variable that separates a lot. Fifteen months later, {c['mal1']}% of loans in 1-30 days had gone bad; {c['mal2']}% of those in 31-60; {c['mal3']}% of those in 61-90. Cures fall from {c['cura1']}% to {c['cura2']}% and {c['cura3']}%. <strong>The useful collections window closes around day 60.</strong></p>
{_div(fig_transicion(d, L), 'g-transicion', L)}
</section>

<section><h2>3. What does moving it cost?</h2>
<p>{e('or')} Moving a threshold means choosing what to lose. Since applications concentrate between 36 and 49, each point of cap removes many people: 45 loses {c['p45']}% of approvals and 43 loses {c['p43']}%. What HMDA does not say is how much delinquency is avoided, because it does not follow loans afterwards.</p>
{tabla_topes(d, L)}
<p>{e('ca')} Bondora does have the real 12-month outcome, so rules can be valued in euros. Delinquency rises with the payment burden, from {c['carga_min']}% to {c['carga_max']}%, but that is not enough to make a cap worthwhile.</p>
{_div(fig_carga(d, L), 'g-carga', L)}
<p>With an assumed cost of {c['costo']} points for funding and operations, payment-burden caps worsen the result: they cut good customers with large loans. By contrast, removing Denmark and Latvia improves it by {c['dl']} €M giving up {c['dl_sale']}% of loans, and removing E to G improves it by {c['eg']} €M giving up {c['eg_sale']}%. <strong>A variable can predict delinquency and still make a bad threshold.</strong> Without that cost no rule improves the result: the conclusion depends on the assumption, and that has to be said.</p>
{_div(fig_reglas(d, L), 'g-reglas', L)}
<p>{e('co')} In collections, the cost is team capacity. With 20% of accounts, working the most delinquent covers {c['cob_atr']}% of the balance that went bad; by expected loss, {c['cob_pe']}%. Almost all of the gain comes from the balance: sorting by balance alone reaches {c['cob_saldo']}%. The simple rule captures most of the value.</p>
{_div(fig_cobertura(d, L), 'g-cobertura', L)}
<p class="nota">Backtest on real outcomes, calibrated on one half of the loans and evaluated on the other. It measures whether collections reach the accounts that go bad, not whether they save them: that takes a control group.</p>
</section>

<section><h2>4. Who does it affect?</h2>
<p>{e('or')} A cap that looks neutral can weigh differently by group. The adverse impact ratio compares each group's approval with the reference group's; below {c['umbral']} it is a warning sign. In conventional loans, Black applicants are already at {c['ai_n']}. With a cap of 45 they fall to {c['ai45n']}; with 43, to {c['ai43n']}, and Hispanic applicants cross the threshold too ({c['ai43h']}).</p>
{_div(fig_impacto(d, L), 'g-impacto', L)}
<p>The denial gap shrinks when comparing similar profiles, but it does not go away: for Black applicants it falls from {c['br_n']} to {c['co_n']} points (95% CI: {c['co_n_i']} to {c['co_n_s']}), and for Hispanic applicants from {c['br_h']} to {c['co_h']} ({c['co_h_i']} to {c['co_h_s']}). For Asian applicants it changes sign, from {c['br_a']} to {c['co_a']}. <strong>This does not prove discrimination:</strong> public HMDA has neither the credit score nor the decision engine's result. It measures how much remains unexplained by what is observed, which is what a policy team has to investigate before applying the rule.</p>
{_div(fig_brecha(d, L), 'g-brecha', L)}
</section>

<section><h2>5. Does it still hold?</h2>
<p>{e('ca')} A threshold is calibrated on the past. Vintages show why it has to be reviewed: 2019 reached much more delinquency than 2022 and 2024 at the same age.</p>
{_div(fig_cosechas(d, L), 'g-cosechas', L)}
<p>The same goes for a segment. Denmark and Latvia lost in every half-year (between {c['dl_max']}% and {c['dl_min']}% of the amount), so that rule is solid. Ratings F and G went from {c['fg_ini']}% to {c['fg_fin']}%: the problem is recent, and the historical average would not have shown it. <strong>That is why a threshold needs monitoring, not just calibration.</strong></p>
{_div(fig_estabilidad(d, L), 'g-estabilidad', L)}
</section>

<section><h2>In Argentina: regulation sets thresholds too</h2>
<p>The five questions apply to regulatory thresholds as well. The central bank (BCRA) classifies consumer debtors by days past due and sets minimum provisions per class. Applied as an exercise to this €{c['saldo']}M portfolio, they come to €{c['bcra']}M against €{c['ecl_b']}-{c['ecl']}M of expected loss. <strong>The total is similar, the mix is not:</strong> in class 1, 1% against {c['s1_e']}%, and in class 5, 100% against {c['s5_e']}%. The rule provisions too little for the healthy and too much for the very old, and the two offset each other.</p>
{_div(fig_previsiones(d, L), 'g-previsiones', L)}
<p>On the macro side, the project <a href="{c['mora_url']}en/">Household loan delinquency in Argentina</a> shows how the approval cutoff shifts when the cycle changes. They are the same thresholds, seen from above.</p>
</section>"""
        titulo_lim = "What these data cannot tell us"
        lim = [
            "HMDA has no score or performance: caps measure approval and volume, not the delinquency avoided. These are mortgages from a single state.",
            "Rules in Bondora can only be evaluated by tightening, because denied applicants are not observed.",
            f"The {c['costo']}-point cost is an assumption and the result covers the first year. A different cost changes the conclusion.",
            "Denmark and Latvia came from looking at these same data: they get confirmed with new vintages.",
            f"There is a single 15-month transition. LGD ranges from {c['lgd_b']}% to {c['lgd']}% depending on the method, which moves expected loss from {c['ecl_b']} to {c['ecl']} €M.",
            "Bondora does not publish collection actions: the effect of collecting and the channels are assumptions, and are not shown as results.",
        ]
    fin = f"<section><h2>{titulo_lim}</h2><ul>{''.join(f'<li>{x}</li>' for x in lim)}</ul></section>"
    return hero, sintesis, secciones + fin


CSS = """
:root{color-scheme:light;--bg:#f9f9f7;--surface:#fcfcfb;--text:#0b0b0b;--text2:#52514e;--muted:#898781;--line:#e1e0d9;--accent:#2a78d6;--lado1:rgba(42,120,214,.075);--lado2:rgba(235,104,52,.055)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#0d0d0d;--surface:#1a1a19;--text:#f0efec;--text2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--accent:#3987e5;--lado1:rgba(57,135,229,.10);--lado2:rgba(217,89,38,.07)}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#0d0d0d;--surface:#1a1a19;--text:#f0efec;--text2:#c3c2b7;--muted:#898781;--line:#2c2c2a;--accent:#3987e5;--lado1:rgba(57,135,229,.10);--lado2:rgba(217,89,38,.07)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}
@media screen and (min-width:1000px){body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
background:radial-gradient(50% 85% at 0% 25%,var(--lado1),transparent 72%),radial-gradient(50% 85% at 100% 75%,var(--lado2),transparent 72%)}}
header{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
h1{font-size:2rem;line-height:1.2;margin:8px 0}
h2{font-size:1.35rem;margin:48px 0 8px}
.sub{color:var(--text2);max-width:720px;margin:0 0 24px}
a{color:var(--accent)}
.idioma{font-size:.9rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px}
.tile-valor{font-size:1.7rem;font-weight:600;line-height:1.1}
.tile-etq{color:var(--text2);font-size:.92rem;margin-top:6px}
.tile-nota{color:var(--muted);font-size:.82rem;margin-top:6px}
section .js-plotly-plot,section .plotly-graph-div{background:var(--surface);border:1px solid var(--line);border-radius:8px;margin:12px 0}
.tabla{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.92rem;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
th{color:var(--text2);font-weight:600}
.nota{color:var(--text2);font-size:.9rem}
.etapa{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;color:var(--text2);border:1px solid var(--line);border-radius:4px;padding:1px 6px;margin-right:4px;vertical-align:1px}
.sintesis{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:4px 20px 8px;margin-top:28px}
.sintesis h2{margin:16px 0 4px}
.sintesis ol{padding-left:20px;margin:8px 0}
.sintesis li{margin:10px 0}
footer{color:var(--muted);font-size:.85rem;margin-top:48px;border-top:1px solid var(--line);padding-top:16px}
"""

JS_TEMA = """
const SERIES=%s, TINTA=%s;
function aplicarTema(){
  const t=document.documentElement.dataset.theme, osc=t?t==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
  const k=osc?1:0, ink=TINTA[osc?'oscuro':'claro'];
  document.querySelectorAll('.js-plotly-plot').forEach(g=>{
    const idx=[],colores=[];
    g.data.forEach((tr,i)=>{const r=tr.meta&&tr.meta.rol;if(r){idx.push(i);colores.push(SERIES[r][k])}});
    if(idx.length)Plotly.restyle(g,{'line.color':colores,'marker.color':colores},idx);
    Plotly.relayout(g,{'font.color':ink.texto,'legend.font.color':ink.secundario,
      'xaxis.tickfont.color':ink.secundario,'yaxis.tickfont.color':ink.secundario,
      'yaxis.title.font.color':ink.secundario,'xaxis.title.font.color':ink.secundario,
      'yaxis.gridcolor':ink.grilla,'xaxis.linecolor':ink.eje,'yaxis.linecolor':ink.eje});
  });
}
window.addEventListener('load',aplicarTema);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',aplicarTema);
"""


def pagina(d: dict, L: str) -> str:
    hero, sintesis, secciones = contenido(d, L)
    cfg = settings()["sitio"]
    repo = cfg["repo_url"]
    es = L == "es"
    titulo = "Umbrales de crédito" if es else "Credit thresholds"
    sub = ("Cómo se decide a quién aprobar, cuánto cobrar y a quién llamar primero, con datos reales del ciclo completo del crédito: originación, cartera y cobranzas."
           if es else "How to decide who to approve, what to charge and who to call first, with real data from the full credit cycle: origination, portfolio and collections.")
    otro = ("English", "en/") if es else ("Español", "../")
    memo = ("memo.pdf", "Memo ejecutivo (PDF)") if es else ("../memo-en.pdf", "Executive memo (PDF)")
    archivo = "umbrales_credito" if es else "umbrales_credito_en"
    tablero = (f"{repo}/raw/main/powerbi/{archivo}.pbix", "Tablero de Power BI (.pbix)" if es else "Power BI dashboard (.pbix)")
    if (ROOT / "powerbi" / f"{archivo}.pdf").exists():
        tablero = ("powerbi.pdf", "Tablero de Power BI (PDF)") if es else ("../powerbi-en.pdf", "Power BI dashboard (PDF)")
    pie = (f"Datos: HMDA (FFIEC/CFPB), Bondora y normas del BCRA, a {mes(d['cartera']['fecha'], L)}. Código y metodología: <a href=\"{repo}\">{repo}</a>."
           if es else f"Data: HMDA (FFIEC/CFPB), Bondora and BCRA rules, as of {mes(d['cartera']['fecha'], L)}. Code and methodology: <a href=\"{repo}\">{repo}</a>.")
    js = JS_TEMA % (json.dumps({k: list(v) for k, v in SERIES.items()}), json.dumps(TINTA))
    return f"""<!doctype html>
<html lang="{L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<meta name="description" content="{sub}">
<style>{CSS}</style>
<script src="{PLOTLY_JS}"></script>
{f'<script src="{PLOTLY_ES}"></script>' if es else ""}
</head>
<body>
<main>
<header><h1>{titulo}</h1><span class="idioma"><a href="{memo[0]}">{memo[1]}</a> · <a href="{tablero[0]}">{tablero[1]}</a> · <a href="{otro[1]}">{otro[0]}</a></span></header>
<p class="sub">{sub}</p>
<div class="tiles">{hero}</div>
{sintesis}
{secciones}
<footer>{pie}</footer>
</main>
<script>{js}</script>
</body>
</html>
"""


def main() -> None:
    d = datos()
    destino = ROOT / settings()["sitio"]["destino"]
    for L, rel in (("es", "index.html"), ("en", "en/index.html")):
        f = destino / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(pagina(d, L), encoding="utf-8")
    for origen, publicado in (("umbrales_credito.pdf", "powerbi.pdf"), ("umbrales_credito_en.pdf", "powerbi-en.pdf")):
        if (ROOT / "powerbi" / origen).exists():
            shutil.copyfile(ROOT / "powerbi" / origen, destino / publicado)
    print(f"sitio: {destino}")


if __name__ == "__main__":
    main()
