"""`python -m ciclo.exportar`: copia los marts a outputs/marts/ en CSV.

Son los archivos que leen Power BI y el sitio, y que se versionan: el warehouse queda fuera de git.
"""

from __future__ import annotations

import duckdb

from ciclo.config import path

MARTS = ["mart_cosechas", "mart_cartera_tramos", "mart_roll_rates", "mart_recupero_observado", "mart_recupero_curva",
         "mart_lgd_pais", "mart_perdida_segmentos", "mart_rentabilidad_cosechas", "mart_previsiones", "mart_embudo",
         "mart_motivos_rechazo", "mart_aprobacion_dti", "mart_brechas", "mart_carga_mora"]


def main() -> None:
    out = path("outputs") / "marts"
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path("warehouse") / "ciclo.duckdb"), read_only=True)
    for m in MARTS:
        con.sql(f"select * from {m} order by all").df().to_csv(out / f"{m}.csv", index=False, float_format="%.4f")
    print(f"exportar: {len(MARTS)} marts en {out}")


if __name__ == "__main__":
    main()
