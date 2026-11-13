# Calculadora FIRE / Coast FIRE

Calculadora em Streamlit que mostra o patrimônio por idade com as curvas:
patrimônio continuando os aportes, patrimônio Coast FIRE, Número Coast FIRE e Número FIRE.
Ela também marca os pontos em que você atinge o Coast FIRE e o FIRE.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Testes: `pytest`

## Premissas
- Capitalização mensal; taxa real = (1 + nominal) / (1 + inflação) − 1.
- Número FIRE = gastos anuais ÷ taxa de retirada segura.
- Número Coast FIRE = Número FIRE descontado pela taxa real até a idade de aposentadoria.
- Aporte mensal constante em poder de compra; sem impostos e sem taxas.
- Os valores podem ser exibidos em reais de hoje ou nominais.
