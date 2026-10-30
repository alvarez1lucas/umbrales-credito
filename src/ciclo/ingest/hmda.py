"""HMDA: solicitudes de crédito hipotecario en EE.UU., aprobadas y rechazadas, con el motivo del rechazo.

Fuente: API del Data Browser del FFIEC/CFPB (pública, sin clave). Cada fila es una solicitud con su
resultado (otorgada, aprobada y no aceptada, rechazada, desistida, incompleta), monto, ingreso,
relación deuda-ingreso, LTV, tasa, prestamista y datos demográficos del solicitante.

Se baja por año y estado (config `hmda`) y se guarda una tabla en data/processed/hmda.parquet con
las columnas que usa el análisis de originación y de préstamo justo.

`python -m ciclo.ingest.hmda` baja lo que falte.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ciclo.config import path, settings
from ciclo.ingest.http import download


def archivo_crudo(anio: int, estado: str) -> Path:
    return path("raw") / "hmda" / f"hmda_{anio}_{estado}.csv"


def bajar(anio: int, estado: str, forzar: bool = False) -> Path:
    cfg = settings()["hmda"]
    destino = archivo_crudo(anio, estado)
    if destino.exists() and not forzar:
        return destino
    params = {"years": anio, "states": estado,
              "loan_purposes": ",".join(map(str, cfg["loan_purposes"])),
              "actions_taken": ",".join(map(str, cfg["actions_taken"]))}
    return download(cfg["api"], destino, params=params)


def leer(archivo: Path, columnas: list[str]) -> pd.DataFrame:
    """Lee un CSV del Data Browser con todo como texto: HMDA mezcla números con rangos ("30%-<36%") y 'Exempt'."""
    df = pd.read_csv(archivo, usecols=columnas, dtype=str)
    for c in ("activity_year", "action_taken", "loan_type", "lien_status", "occupancy_type",
              "applicant_credit_score_type", "aus-1", "denial_reason-1", "denial_reason-2"):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in ("loan_amount", "income", "tract_minority_population_percent", "tract_to_msa_income_percentage"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def update() -> Path:
    cfg = settings()["hmda"]
    partes = []
    for anio in cfg["anios"]:
        for estado in cfg["estados"]:
            partes.append(leer(bajar(anio, estado), cfg["columnas"]).assign(state_code=estado))
    df = pd.concat(partes, ignore_index=True)
    destino = path("processed") / "hmda.parquet"
    df.to_parquet(destino, index=False, compression="zstd")
    print(f"hmda: {len(df):,} solicitudes ({', '.join(map(str, cfg['anios']))}; {', '.join(cfg['estados'])}) → {destino}")
    return destino


if __name__ == "__main__":
    update()
