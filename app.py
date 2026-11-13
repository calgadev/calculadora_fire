import plotly.graph_objects as go
import streamlit as st

from fire_calc import simular

st.set_page_config(page_title="Calculadora FIRE", page_icon="🔥", layout="wide")


def brl(valor: float) -> str:
    texto = f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def idade_txt(idade: float | None) -> str:
    if idade is None:
        return "Não atingido"
    meses_total = round(idade * 12)
    anos, meses = divmod(meses_total, 12)
    return f"{anos} anos" + (f" e {meses} {'mês' if meses == 1 else 'meses'}" if meses else "")


# ----------------------------------------------------------------- entradas
with st.sidebar:
    st.header("Parâmetros")
    idade_atual = st.number_input("Idade Atual", 0, 99, 30, step=1)
    idade_aposentadoria = st.number_input("Idade de Aposentadoria", 1, 100, 60, step=1)
    gastos = st.number_input(
        "Gastos Anuais na Aposentadoria (R$ de hoje)", 0.0, value=120_000.0, step=5_000.0, format="%.2f"
    )
    patrimonio = st.number_input(
        "Patrimônio investido atual (R$)", 0.0, value=100_000.0, step=10_000.0, format="%.2f"
    )
    aporte = st.number_input(
        "Aporte Mensal (R$ de hoje)", 0.0, value=3_000.0, step=500.0, format="%.2f"
    )
    rent = st.number_input("Rentabilidade Anual nominal (%)", -50.0, 100.0, 10.0, step=0.5)
    inflacao = st.number_input("Inflação Anual (%)", -50.0, 100.0, 4.5, step=0.5)
    swr = st.number_input("Taxa de retirada segura (%)", 0.1, 20.0, 4.0, step=0.25)

st.title("🔥 Calculadora FIRE / Coast FIRE")

if idade_aposentadoria <= idade_atual:
    st.error("A idade de aposentadoria deve ser maior que a idade atual.")
    st.stop()

try:
    res = simular(
        idade_atual, idade_aposentadoria, gastos, patrimonio, aporte,
        rent / 100, inflacao / 100, swr / 100,
    )
except ValueError as e:
    st.error(str(e))
    st.stop()

modo = st.radio("Exibir valores em", ["Reais de hoje", "Nominal"], horizontal=True)
suf = "real" if modo == "Reais de hoje" else "nominal"
df = res.df

# ------------------------------------------------------------------ cartões
def valor_no_mes(coluna: str, mes: int) -> float:
    return float(df[f"{coluna}_{suf}"].iloc[mes])


ret_mes = round((idade_aposentadoria - idade_atual) * 12)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    "Número FIRE",
    brl(res.numero_fire if suf == "real" else valor_no_mes("numero_fire", min(ret_mes, len(df) - 1))),
    help="Gastos anuais ÷ taxa de retirada segura"
    + ("" if suf == "real" else " (valor nominal na idade de aposentadoria)"),
)
c2.metric("Número Coast FIRE hoje", brl(res.numero_coast_hoje),
          help="Quanto você precisaria ter hoje para parar de aportar e ainda atingir o FIRE na idade de aposentadoria")
c3.metric("Atinge o Coast FIRE aos", idade_txt(res.idade_coast))
c4.metric("Atinge o FIRE aos", idade_txt(res.idade_fire), help="Mantendo os aportes")
c5.metric("Rentabilidade real anual", f"{res.taxa_real_anual * 100:.2f}%".replace(".", ","))

if res.taxa_real_anual <= 0:
    st.warning("A rentabilidade real (descontada a inflação) é zero ou negativa: o patrimônio não cresce em poder de compra.")
if res.idade_coast is None:
    st.warning("O Coast FIRE não é atingido até os 100 anos com esses parâmetros.")
elif res.idade_fire is None:
    st.warning("O FIRE não é atingido até os 100 anos com esses parâmetros.")

# ------------------------------------------------------------------- gráfico
fig = go.Figure()
hover = "%{customdata}<extra>%{fullData.name}</extra>"


def linha(coluna: str, nome: str, cor: str, dash: str = "solid", largura: float = 3):
    y = df[f"{coluna}_{suf}"]
    fig.add_trace(go.Scatter(
        x=df["idade"], y=y, name=nome, mode="lines",
        line=dict(color=cor, dash=dash, width=largura),
        customdata=[brl(v) if v == v else "" for v in y], hovertemplate=hover,
    ))


linha("aportes", "Patrimônio continuando os aportes", "#2563eb")
linha("coast", "Patrimônio Coast FIRE", "#16a34a")
linha("numero_coast", "Número Coast FIRE", "#f59e0b", dash="dash", largura=2)
linha("numero_fire", "Número FIRE", "#dc2626", dash="dash", largura=2)


def marcar(mes: int | None, nome: str, cor: str, simbolo: str):
    if mes is None or mes >= len(df):
        return
    x, y = df["idade"].iloc[mes], valor_no_mes("aportes", mes)
    fig.add_trace(go.Scatter(
        x=[x], y=[y], name=nome, mode="markers",
        marker=dict(color=cor, size=14, symbol=simbolo, line=dict(color="white", width=2)),
        customdata=[f"{idade_txt(x)} · {brl(y)}"], hovertemplate=hover,
    ))
    fig.add_annotation(x=x, y=y, text=f"<b>{nome}</b><br>{idade_txt(x)}<br>{brl(y)}",
                       showarrow=True, arrowhead=2, ax=-60, ay=-50,
                       bgcolor="rgba(255,255,255,0.85)", bordercolor=cor, font=dict(color="#111"))


marcar(res.mes_coast, "Coast FIRE", "#16a34a", "diamond")
marcar(res.mes_fire, "FIRE", "#dc2626", "star")

fig.add_vline(x=idade_aposentadoria, line_dash="dot", line_color="gray",
              annotation_text="Aposentadoria", annotation_position="top left")
fig.update_layout(
    height=600, hovermode="x unified",
    xaxis_title="Idade (anos)",
    yaxis_title=f"Patrimônio (R$ {'de hoje' if suf == 'real' else 'nominais'})",
    legend=dict(orientation="h", y=-0.15),
    separators=",.", yaxis_tickprefix="R$ ", yaxis_tickformat=",.0f",
    margin=dict(t=30),
)
st.plotly_chart(fig, width="stretch")

st.caption(
    "Premissas: capitalização mensal; aporte mensal constante em poder de compra (corrigido pela inflação); "
    "sem impostos, taxas ou retiradas antes do FIRE. A curva Coast FIRE para de aportar no ponto Coast FIRE "
    "e segue apenas rendendo. Nos valores nominais, o Número FIRE cresce com a inflação."
)
