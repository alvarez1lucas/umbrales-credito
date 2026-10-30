"""Bondora: foto de la cartera completa de préstamos de consumo, crédito por crédito.

Fuente: el "Loan dataset" de las estadísticas públicas de Bondora (Excel, ~175 MB, ~850 mil créditos
otorgados desde 2009 en Finlandia, Estonia, Países Bajos, España y otros países). Cada crédito trae
monto, tasa, plazo, rating y su estado *a la fecha de publicación*: días de atraso, fecha de inicio
del atraso, meses en default, capital e intereses pagados.

Es una foto, no una historia mensual. Por eso cada publicación se guarda como una foto fechada
(data/snapshots/bondora_AAAA-MM-DD.parquet): comparando fotos sucesivas se miden las roll rates
(cuánto pasa de un tramo de atraso al siguiente) y el recupero después del default. Además de la
publicación vigente se usan las fotos viejas que quedaron en la Wayback Machine (config `archivadas`).

`python -m ciclo.ingest.bondora` baja la publicación vigente si todavía no está guardada.
"""

from __future__ import annotations

import re
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd

from ciclo.config import path, settings
from ciclo.ingest.http import download, session

FECHAS = ["loan_issued_at", "early_repaid_at", "loan_last_recorded_action_date_local",
          "next_payment_date_local", "debt_occured_date_local"]
ENTEROS = ["nr_of_payments", "initial_loan_duration"]
FLAGS = ["is_early_repaid_within_14_days", "is_default", "has_default_within_12_months"]
RENOMBRES = {"loan_last_date_local": "loan_last_recorded_action_date_local"}  # nombre en publicaciones de 2025


def fecha_publicacion() -> date:
    """Fecha de la publicación vigente, según el encabezado Last-Modified del archivo."""
    r = session().head(settings()["bondora"]["url"], timeout=settings()["http"]["timeout"])
    r.raise_for_status()
    return parsedate_to_datetime(r.headers["Last-Modified"]).date()


def archivo_foto(fecha: date) -> Path:
    return path("snapshots") / f"bondora_{fecha.isoformat()}.parquet"


def fotos() -> list[Path]:
    """Fotos guardadas, de la más vieja a la más nueva."""
    return sorted(p for p in path("snapshots").glob("bondora_*.parquet") if re.fullmatch(r"bondora_\d{4}-\d{2}-\d{2}\.parquet", p.name))


def fecha_corte(df: pd.DataFrame, publicacion: date) -> pd.Timestamp:
    """Fecha real de los datos: inicio del atraso + días de atraso de los activos, que da el mismo día en todos.

    Sale días o semanas antes de la publicación. Sin créditos atrasados, se usa la publicación.
    """
    a = df[(df["loan_status"] == "Active") & df["debt_occured_date_local"].notna() & (df["days_past_due_principal"] > 0)]
    if a.empty:
        return pd.Timestamp(publicacion)
    return (a["debt_occured_date_local"] + pd.to_timedelta(a["days_past_due_principal"], unit="D")).dt.normalize().mode().iloc[0]


def normalizar(df: pd.DataFrame, fecha: date) -> pd.DataFrame:
    """Tipos consistentes entre fotos: fechas sin hora, flags como booleanos nulos, y la fecha de corte de la foto."""
    df = df.rename(columns=RENOMBRES).copy()
    for c in FECHAS:  # el archivo rellena con 1970-01-01 (época Unix) las fechas que no tiene
        df[c] = pd.to_datetime(df[c], errors="coerce")
        df[c] = df[c].where(df[c].dt.year > 1970)
    for c in FLAGS:
        df[c] = df[c].map({1: True, 0: False, 1.0: True, 0.0: False}).astype("boolean")
    for c in ENTEROS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df["customer_risk_rating"] = df["customer_risk_rating"].astype("string")
    df.insert(0, "fecha_foto", fecha_corte(df, fecha))
    return df


def guardar_foto(url: str, fecha: date, forzar: bool = False) -> Path:
    destino = archivo_foto(fecha)
    if destino.exists() and not forzar:
        print(f"bondora: la foto del {fecha} ya está guardada")
        return destino
    xlsx = download(url, path("raw") / "bondora" / f"loan_dataset_{fecha.isoformat()}.xlsx")
    df = normalizar(pd.read_excel(xlsx, engine="calamine"), fecha)
    df.to_parquet(destino, index=False, compression="zstd")
    print(f"bondora: {len(df):,} créditos, foto del {fecha} → {destino}")
    return destino


def update(forzar: bool = False) -> Path:
    """Fotos archivadas de config (Wayback Machine) y la publicación vigente."""
    cfg = settings()["bondora"]
    for a in cfg["archivadas"]:
        guardar_foto(a["url"], a["fecha"], forzar)
    return guardar_foto(cfg["url"], fecha_publicacion(), forzar)


if __name__ == "__main__":
    update()
