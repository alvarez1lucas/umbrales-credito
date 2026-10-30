import pytest

from ciclo import memo, sitio


@pytest.fixture(scope="module")
def d():
    return sitio.datos()


def test_num_respeta_el_idioma():
    assert sitio.num(1234.5, "es") == "1.234,5"
    assert sitio.num(1234.5, "en") == "1,234.5"


@pytest.mark.parametrize("L", ["es", "en"])
def test_paginas_se_generan_desde_outputs(d, L):
    html = sitio.pagina(d, L)
    assert html.count('class="plotly-graph-div"') == 13
    assert "nan" not in sitio.cifras(d, L).values()


@pytest.mark.parametrize("L", ["es", "en"])
def test_memo_y_readme_sin_campos_vacios(d, L):
    for texto in (memo.memo_html(d, L), memo.readme(d, L)):
        assert "{c[" not in texto and "None" not in texto
