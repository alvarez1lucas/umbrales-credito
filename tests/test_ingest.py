from datetime import date

import pandas as pd

from ciclo.ingest import bondora, hmda


def _fila_bondora(**cambios):
    fila = {c: None for c in bondora.FECHAS + bondora.ENTEROS + bondora.FLAGS}
    fila.update({"loan_status": "Repaid", "days_past_due_principal": 0.0,
                 "loan_issued_at": "2024-01-15 10:00:00", "debt_occured_date_local": "1970-01-01",
                 "next_payment_date_local": "2026-11-18", "is_default": 1.0, "is_early_repaid_within_14_days": 0,
                 "has_default_within_12_months": None, "nr_of_payments": 12.0, "initial_loan_duration": 36,
                 "customer_risk_rating": "B"})
    fila.update(cambios)
    return pd.DataFrame([fila])


def test_normalizar_fechas_de_relleno_son_nulas():
    df = bondora.normalizar(_fila_bondora(), date(2026, 10, 26))
    assert pd.isna(df.loc[0, "debt_occured_date_local"])
    assert df.loc[0, "next_payment_date_local"] == pd.Timestamp("2026-11-18")


def test_normalizar_flags_y_fecha_de_foto():
    df = bondora.normalizar(_fila_bondora(), date(2026, 10, 26))
    assert df.columns[0] == "fecha_foto" and df.loc[0, "fecha_foto"] == pd.Timestamp("2026-10-26")
    assert bool(df.loc[0, "is_default"])
    assert not bool(df.loc[0, "is_early_repaid_within_14_days"])
    assert pd.isna(df.loc[0, "has_default_within_12_months"])
    assert df["nr_of_payments"].dtype == "Int64"


def test_normalizar_renombra_columna_de_publicaciones_viejas():
    fila = _fila_bondora(loan_last_date_local="2025-08-01").drop(columns="loan_last_recorded_action_date_local")
    df = bondora.normalizar(fila, date(2025, 8, 18))
    assert df.loc[0, "loan_last_recorded_action_date_local"] == pd.Timestamp("2025-08-01")


def test_fecha_corte_sale_de_los_activos_atrasados():
    df = pd.DataFrame({"loan_status": ["Active", "Active", "Active", "Repaid"],
                       "debt_occured_date_local": pd.to_datetime(["2026-10-01", "2026-09-22", "2026-10-11", "2020-01-01"]),
                       "days_past_due_principal": [21.0, 30.0, 11.0, 900.0]})
    assert bondora.fecha_corte(df, date(2026, 10, 26)) == pd.Timestamp("2026-10-22")


def test_archivo_foto_por_fecha():
    assert bondora.archivo_foto(date(2026, 10, 26)).name == "bondora_2026-10-26.parquet"


def test_hmda_leer_mantiene_rangos_como_texto(tmp_path):
    cols = ["activity_year", "action_taken", "loan_type", "lien_status", "occupancy_type",
            "applicant_credit_score_type", "aus-1", "denial_reason-1", "denial_reason-2", "loan_amount", "income",
            "tract_minority_population_percent", "tract_to_msa_income_percentage", "debt_to_income_ratio",
            "loan_to_value_ratio"]
    f = tmp_path / "h.csv"
    pd.DataFrame([["2024", "3", "1", "1", "1", "9", "1", "1", "", "255000", "88", "40.1", "95", "30%-<36%", "Exempt"]],
                 columns=cols).to_csv(f, index=False)
    df = hmda.leer(f, cols)
    assert df.loc[0, "debt_to_income_ratio"] == "30%-<36%"
    assert df.loc[0, "loan_to_value_ratio"] == "Exempt"
    assert df.loc[0, "denial_reason-1"] == 1 and pd.isna(df.loc[0, "denial_reason-2"])
    assert df.loc[0, "loan_amount"] == 255000
