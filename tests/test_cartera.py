import pandas as pd
import pytest

from ciclo import cartera


def test_indicadores_mora():
    t = pd.DataFrame({"tramo": ["al_dia", "1-30", "31-60", "61-90", "90+"], "saldo_capital": [600.0, 100.0, 50.0, 50.0, 200.0]})
    m = cartera.indicadores_mora(t)
    assert m["par30_pct"] == pytest.approx(30) and m["par90_pct"] == pytest.approx(20)
    assert m["atraso_31_90_sobre_no_vencida_pct"] == pytest.approx(12.5)


def test_concentracion():
    c = cartera.concentracion(pd.Series({"a": 75.0, "b": 25.0}))
    assert c["hhi"] == pytest.approx(0.625)
    assert c["participacion_pct"]["a"] == 75


def test_ecl_reescala_solo_etapas_que_dependen_de_lgd():
    p = pd.DataFrame({"etapa": [1, 2, 3], "perdida_esperada": [10.0, 30.0, 100.0]})
    assert cartera.ecl_con_otra_lgd(p, 80, 40) == pytest.approx(120)
