"""Lógica de cálculo FIRE / Coast FIRE (sem dependência de interface).

Toda a simulação é feita mensalmente em termos reais (reais de hoje).
As séries nominais são obtidas multiplicando as reais pelo fator de inflação
acumulada (1 + i_m)^t.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

IDADE_MAXIMA = 100
ANOS_APOS_HORIZONTE = 5


@dataclass
class Resultado:
    df: pd.DataFrame
    numero_fire: float
    numero_coast_hoje: float
    taxa_real_anual: float
    mes_coast: int | None
    idade_coast: float | None
    mes_fire: int | None
    idade_fire: float | None


def taxa_real_anual(rentabilidade_nominal: float, inflacao: float) -> float:
    return (1 + rentabilidade_nominal) / (1 + inflacao) - 1


def simular(
    idade_atual: float,
    idade_aposentadoria: float,
    gastos_anuais: float,
    patrimonio_atual: float,
    aporte_mensal: float,
    rentabilidade_nominal: float,
    inflacao: float,
    taxa_retirada: float,
) -> Resultado:
    """Simula as curvas FIRE / Coast FIRE.

    Taxas em fração decimal (ex.: 0.10 para 10%). Valores monetários em
    reais de hoje; o aporte mensal é mantido constante em termos reais.
    """
    if taxa_retirada <= 0:
        raise ValueError("A taxa de retirada segura deve ser maior que zero.")
    if inflacao <= -1 or rentabilidade_nominal <= -1:
        raise ValueError("Taxas devem ser maiores que -100%.")
    if idade_atual >= IDADE_MAXIMA:
        raise ValueError(f"A idade atual deve ser menor que {IDADE_MAXIMA}.")

    r_real = taxa_real_anual(rentabilidade_nominal, inflacao)
    r_m = (1 + r_real) ** (1 / 12) - 1
    i_m = (1 + inflacao) ** (1 / 12) - 1
    numero_fire = gastos_anuais / taxa_retirada

    meses_ate_aposentadoria = max(0, round((idade_aposentadoria - idade_atual) * 12))
    meses_max = round((IDADE_MAXIMA - idade_atual) * 12)

    # 1) Patrimônio continuando os aportes, até o limite máximo de idade.
    t = np.arange(meses_max + 1)
    p_aportes = np.empty(meses_max + 1)
    p_aportes[0] = patrimonio_atual
    for k in range(1, meses_max + 1):
        p_aportes[k] = p_aportes[k - 1] * (1 + r_m) + aporte_mensal

    # 2) Número Coast FIRE (desconta o Número FIRE até a aposentadoria).
    meses_restantes = np.clip(meses_ate_aposentadoria - t, 0, None)
    numero_coast = numero_fire / (1 + r_m) ** meses_restantes

    # 3) Pontos de Coast FIRE e FIRE.
    mes_coast = _primeiro_indice(p_aportes >= numero_coast)
    mes_fire = _primeiro_indice(p_aportes >= numero_fire)

    # 4) Horizonte do gráfico.
    fim_anos = max(idade_aposentadoria, idade_atual)
    if mes_fire is not None:
        fim_anos = max(fim_anos, idade_atual + mes_fire / 12)
    meses_horizonte = min(
        meses_max, round((fim_anos + ANOS_APOS_HORIZONTE - idade_atual) * 12)
    )
    n = meses_horizonte + 1
    t = t[:n]
    p_aportes = p_aportes[:n]
    numero_coast = numero_coast[:n]

    # 5) Patrimônio Coast FIRE: segue os aportes até o ponto Coast e depois
    #    cresce apenas com a rentabilidade.
    p_coast = p_aportes.copy()
    if mes_coast is not None and mes_coast < n:
        p_coast[mes_coast:] = p_aportes[mes_coast] * (1 + r_m) ** (
            t[mes_coast:] - mes_coast
        )
    else:
        p_coast[:] = np.nan

    fator_inflacao = (1 + i_m) ** t
    df = pd.DataFrame(
        {
            "mes": t,
            "idade": idade_atual + t / 12,
            "fator_inflacao": fator_inflacao,
            "aportes_real": p_aportes,
            "coast_real": p_coast,
            "numero_coast_real": numero_coast,
            "numero_fire_real": np.full(n, numero_fire),
        }
    )
    for serie in ("aportes", "coast", "numero_coast", "numero_fire"):
        df[f"{serie}_nominal"] = df[f"{serie}_real"] * fator_inflacao

    return Resultado(
        df=df,
        numero_fire=numero_fire,
        numero_coast_hoje=float(numero_coast[0]),
        taxa_real_anual=r_real,
        mes_coast=mes_coast,
        idade_coast=None if mes_coast is None else idade_atual + mes_coast / 12,
        mes_fire=mes_fire,
        idade_fire=None if mes_fire is None else idade_atual + mes_fire / 12,
    )


def _primeiro_indice(mascara: np.ndarray) -> int | None:
    idx = np.flatnonzero(mascara)
    return int(idx[0]) if idx.size else None
