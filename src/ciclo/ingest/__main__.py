"""`python -m ciclo.ingest`: actualiza todas las fuentes."""

from ciclo.ingest import bondora, hmda

bondora.update()
hmda.update()
