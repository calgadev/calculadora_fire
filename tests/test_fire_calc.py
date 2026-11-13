import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fire_calc import simular  # noqa: E402

BASE = dict(
    idade_atual=30, idade_aposentadoria=60, gastos_anuais=60_000,
    patrimonio_atual=50_000, aporte_mensal=2_000,
    rentabilidade_nominal=0.10, inflacao=0.04, taxa_retirada=0.04,
)


def test_numero_fire():
    assert simular(**BASE).numero_fire == pytest.approx(1_500_000)


def test_coast_atinge_fire_na_aposentadoria():
    res = simular(**BASE)
    assert res.mes_coast is not None
    linha = res.df.loc[res.df["mes"] == 30 * 12].iloc[0]
    assert linha["coast_real"] >= res.numero_fire
    assert linha["coast_real"] == pytest.approx(res.numero_fire, rel=0.01)


def test_ja_coast_hoje():
    res = simular(**{**BASE, "patrimonio_atual": 1_000_000})
    assert res.mes_coast == 0
    assert res.idade_coast == 30


def test_nominal_igual_real_vezes_inflacao():
    df = simular(**BASE).df
    i_m = 1.04 ** (1 / 12) - 1
    np.testing.assert_allclose(df["aportes_nominal"], df["aportes_real"] * (1 + i_m) ** df["mes"])
    assert df["numero_fire_nominal"].iloc[12] == pytest.approx(1_500_000 * 1.04)


def test_sem_aporte_nao_atinge():
    res = simular(**{**BASE, "aporte_mensal": 0, "patrimonio_atual": 1_000, "rentabilidade_nominal": 0.04})
    assert res.mes_fire is None
    assert res.mes_coast is None


def test_juros_compostos_a_mao():
    # 12 meses, taxa real de 1% a.m. (1,01^12 a.a.); aporte 100
    res = simular(**{**BASE, "rentabilidade_nominal": 1.01**12 * 1.04 - 1, "patrimonio_atual": 1_000,
                     "aporte_mensal": 100})
    esperado = 1_000 * 1.01**12 + 100 * (1.01**12 - 1) / 0.01
    assert res.df["aportes_real"].iloc[12] == pytest.approx(esperado)


def test_taxa_retirada_invalida():
    with pytest.raises(ValueError):
        simular(**{**BASE, "taxa_retirada": 0})
