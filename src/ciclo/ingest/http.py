"""Sesión HTTP con reintentos, compartida por los módulos de ingesta.

Los certificados se validan contra el almacén del sistema operativo (truststore): así funciona
detrás de antivirus o proxies que inspeccionan TLS, sin desactivar la verificación.
"""

from __future__ import annotations

import ssl
import time
from functools import lru_cache
from pathlib import Path

import requests
import truststore
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ciclo.config import settings


class _SystemTrustAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return super().init_poolmanager(*args, **kwargs)


@lru_cache(maxsize=1)
def session() -> requests.Session:
    cfg = settings()["http"]
    retry = Retry(total=cfg["retries"], backoff_factor=cfg["backoff"],
                  status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET", "HEAD"))
    s = requests.Session()
    s.headers["User-Agent"] = cfg["user_agent"]
    s.mount("https://", _SystemTrustAdapter(max_retries=retry))
    return s


def download(url: str, dest: Path, params: dict | None = None) -> Path:
    """Baja `url` a `dest` en streaming; reintenta la transferencia completa si se corta."""
    cfg = settings()["http"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(cfg["retries"] + 1):
        try:
            with session().get(url, params=params, stream=True, timeout=cfg["timeout"]) as r:
                r.raise_for_status()
                if "text/html" in r.headers.get("Content-Type", ""):
                    raise FileNotFoundError(f"El servidor devolvió HTML para {url}")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
            break
        except (requests.ConnectionError, requests.exceptions.ChunkedEncodingError):
            tmp.unlink(missing_ok=True)
            if attempt == cfg["retries"]:
                raise
            time.sleep(cfg["backoff"] * 2**attempt)
    tmp.replace(dest)
    return dest
