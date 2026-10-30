"""`python -m ciclo.modelos`: construye el warehouse con dbt (modelos y tests) desde la raíz del repo."""

from __future__ import annotations

import os
import sys

from dbt.cli.main import dbtRunner

from ciclo.config import ROOT, path


def build(seleccion: list[str] | None = None) -> bool:
    path("warehouse")
    os.chdir(ROOT)  # las rutas a los parquet en las fuentes son relativas a la raíz
    args = ["build", "--project-dir", "dbt_ciclo", "--profiles-dir", "dbt_ciclo"]
    if seleccion:
        args += ["--select", *seleccion]
    return dbtRunner().invoke(args).success


if __name__ == "__main__":
    sys.exit(0 if build(sys.argv[1:] or None) else 1)
