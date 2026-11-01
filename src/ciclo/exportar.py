"""`python -m ciclo.exportar`: copia los marts a outputs/marts/ en CSV.

Son los archivos que leen Power BI y el sitio, y que se versionan: el warehouse queda fuera de git.
"""

from __future__ import annotations

import duckdb

from ciclo.config import path

MARTS = ["mart_cosechas", "mart_cartera_tramos", "mart_roll_rates", "mart_recupero_observado", "mart_recupero_curva",
         "mart_lgd_pais", "mart_perdida_segmentos", "mart_rentabilidad_cosechas", "mart_previsiones", "mart_embudo",
         "mart_motivos_rechazo", "mart_aprobacion_dti", "mart_brechas", "mart_carga_mora", "mart_composicion", "mart_deterioro"]


DIMENSIONES = {
    "dim_tramo": "select * from (values ('al_dia', 1, 'Al día'), ('1-30', 2, '1-30 días'), ('31-60', 3, '31-60 días'), ('61-90', 4, '61-90 días'), ('90+', 5, '90+ días'), ('pagado', 6, 'Pagado'), ('castigado', 7, 'Castigado')) t(tramo, orden, nombre)",
    "dim_rating": "select * from (values ('AA', 1), ('A', 2), ('B', 3), ('C', 4), ('D', 5), ('E', 6), ('F', 7), ('G', 8), ('HR', 9), ('sin_rating', 10)) t(rating, orden)",
    "dim_pais": "select distinct pais from mart_cartera_tramos order by pais",
    "dim_situacion": "select situacion, nombre, dias_desde, dias_hasta, prevision_sin_garantia_pct from bcra_situaciones order by situacion",
}


def main() -> None:
    out = path("outputs") / "marts"
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path("warehouse") / "ciclo.duckdb"), read_only=True)
    for m in MARTS:
        con.sql(f"select * from {m} order by all").df().to_csv(out / f"{m}.csv", index=False, float_format="%.4f")
    for nombre, consulta in DIMENSIONES.items():
        con.sql(consulta).df().to_csv(out / f"{nombre}.csv", index=False)
    print(f"exportar: {len(MARTS)} marts y {len(DIMENSIONES)} dimensiones en {out}")


if __name__ == "__main__":
    main()
