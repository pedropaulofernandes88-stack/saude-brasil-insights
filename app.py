"""Painel interativo do projeto Saude Brasil Insights."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "processed"

METRICS = {
    "Índice de lacuna assistencial": "indice_lacuna",
    "UBS por 10 mil habitantes": "ubs_por_10k",
    "Hospitais por 100 mil habitantes": "hospitais_por_100k",
    "Distância proxy até município com hospital": "distancia_hospital_proxy_km",
    "Centros cirúrgicos por 100 mil habitantes": "centros_cirurgicos_por_100k",
    "Centros obstétricos por 100 mil habitantes": "centros_obstetricos_por_100k",
}

METRIC_HELP = {
    "indice_lacuna": "0 indica maior disponibilidade relativa e 100, maior lacuna relativa.",
    "ubs_por_10k": "Quantidade de UBS cadastradas para cada 10 mil habitantes.",
    "hospitais_por_100k": "Quantidade de hospitais para cada 100 mil habitantes.",
    "distancia_hospital_proxy_km": (
        "Distância geodésica entre centros municipais; não é distância viária nem tempo de viagem."
    ),
    "centros_cirurgicos_por_100k": "Hospitais com centro cirúrgico por 100 mil habitantes.",
    "centros_obstetricos_por_100k": "Hospitais com centro obstétrico por 100 mil habitantes.",
}

SENSITIVITY_SCENARIOS = {
    "0% UBS / 100% hospitais": "indice_lacuna_peso_ubs_000",
    "25% UBS / 75% hospitais": "indice_lacuna_peso_ubs_025",
    "50% UBS / 50% hospitais": "indice_lacuna_peso_ubs_050",
    "65% UBS / 35% hospitais (principal)": "indice_lacuna_peso_ubs_065",
    "75% UBS / 25% hospitais": "indice_lacuna_peso_ubs_075",
    "100% UBS / 0% hospitais": "indice_lacuna_peso_ubs_100",
}


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, dict, dict]:
    frame = pd.read_csv(DATA_DIR / "municipios.csv", dtype={"ibge7": "string", "ibge6": "string"})
    geojson = json.loads((DATA_DIR / "municipios.geojson").read_text(encoding="utf-8"))
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    return frame, geojson, metadata


def format_integer(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_decimal(value: float | int) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.set_page_config(
    page_title="Saúde Brasil Insights",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #f6f8f7; }
      [data-testid="stSidebar"] { background: #0b2f33; }
      [data-testid="stSidebar"] * { color: #f4fbf8; }
      [data-testid="stMetric"] {
        background: white;
        border: 1px solid #dfe9e5;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(11,47,51,.05);
      }
      .hero {
        padding: 24px 28px;
        border-radius: 18px;
        color: white;
        background: linear-gradient(120deg, #0b2f33 0%, #12665e 65%, #24a17e 100%);
        margin-bottom: 18px;
      }
      .hero h1 { margin: 0 0 6px 0; font-size: 2rem; }
      .hero p { margin: 0; opacity: .88; max-width: 850px; }
      .notice {
        background: #fff8e7;
        border-left: 4px solid #e0a329;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 8px 0 18px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

required_files = [
    DATA_DIR / "municipios.csv",
    DATA_DIR / "municipios.geojson",
    DATA_DIR / "metadata.json",
]
if not all(path.exists() for path in required_files):
    st.error(
        "Snapshot não encontrado. Execute `saude-brasil-update --output-dir data/processed` "
        "antes de iniciar o painel."
    )
    st.stop()

data, geojson, metadata = load_data()

st.markdown(
    """
    <div class="hero">
      <h1>Saúde Brasil Insights</h1>
      <p>Uma leitura exploratória da disponibilidade municipal de UBS e hospitais ativos,
      combinando dados oficiais do Ministério da Saúde e do IBGE.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Filtros")
    selected_regions = st.multiselect(
        "Região",
        options=sorted(data["regiao"].unique()),
        default=sorted(data["regiao"].unique()),
    )
    available_ufs = sorted(data.loc[data["regiao"].isin(selected_regions), "uf"].unique())
    selected_ufs = st.multiselect("UF", options=available_ufs, default=available_ufs)
    min_population = st.number_input(
        "População mínima",
        min_value=0,
        max_value=1_000_000,
        value=0,
        step=10_000,
        help="Ajuda a comparar municípios de portes semelhantes.",
    )
    metric_label = st.selectbox("Indicador do mapa", options=list(METRICS))
    metric = METRICS[metric_label]
    if metric == "indice_lacuna":
        scenario = st.selectbox(
            "Cenário do índice",
            options=list(SENSITIVITY_SCENARIOS),
            index=3,
            help="Permite verificar se a conclusão muda com os pesos de UBS e hospitais.",
        )
        metric = SENSITIVITY_SCENARIOS[scenario]
    st.caption(METRIC_HELP[METRICS[metric_label]])
    st.divider()
    st.caption(f"População de referência: {metadata['population_year']}")
    generated_date = metadata["generated_at_utc"][:10]
    st.caption(f"Snapshot gerado em: {generated_date}")

filtered = data.loc[
    data["regiao"].isin(selected_regions)
    & data["uf"].isin(selected_ufs)
    & data["populacao"].ge(min_population)
].copy()

if filtered.empty:
    st.warning("Nenhum município corresponde aos filtros escolhidos.")
    st.stop()

st.markdown(
    """
    <div class="notice"><strong>Leitura correta:</strong> o índice é comparativo e exploratório.
    Ele não confirma sozinho um vazio assistencial nem substitui análise de redes regionais,
    deslocamento, demanda, qualidade ou capacidade operacional.</div>
    """,
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Municípios", format_integer(len(filtered)))
kpi2.metric("População", format_integer(filtered["populacao"].sum()))
kpi3.metric("UBS cadastradas", format_integer(filtered["ubs"].sum()))
kpi4.metric("Hospitais ativos", format_integer(filtered["hospitais"].sum()))

st.subheader("Distribuição municipal")
color_scale = "YlOrRd" if metric.startswith("indice_lacuna") else "Tealgrn"
map_figure = px.choropleth(
    filtered,
    geojson=geojson,
    locations="ibge7",
    featureidkey="properties.codarea",
    color=metric,
    color_continuous_scale=color_scale,
    hover_name="municipio",
    hover_data={
        "ibge7": False,
        "uf": True,
        "populacao": ":,.0f",
        "ubs_por_10k": ":.2f",
        "hospitais_por_100k": ":.2f",
        "indice_lacuna": ":.2f",
    },
    labels={
        metric: metric_label,
        "uf": "UF",
        "populacao": "População",
        "ubs_por_10k": "UBS / 10 mil",
        "hospitais_por_100k": "Hospitais / 100 mil",
        "indice_lacuna": "Índice de lacuna",
    },
)
map_figure.update_geos(fitbounds="locations", visible=False)
map_figure.update_layout(
    height=610,
    margin={"r": 0, "t": 10, "l": 0, "b": 0},
    paper_bgcolor="rgba(0,0,0,0)",
    coloraxis_colorbar={"title": metric_label, "thickness": 14},
)
st.plotly_chart(map_figure, width="stretch", config={"displaylogo": False})

left, right = st.columns([1, 1])
with left:
    st.subheader("Maiores lacunas relativas")
    ranking = filtered.nlargest(15, "indice_lacuna").sort_values("indice_lacuna")
    ranking["local"] = ranking["municipio"] + " — " + ranking["uf"]
    bar_figure = px.bar(
        ranking,
        x="indice_lacuna",
        y="local",
        orientation="h",
        color="indice_lacuna",
        color_continuous_scale="YlOrRd",
        labels={"indice_lacuna": "Índice de lacuna", "local": ""},
    )
    bar_figure.update_layout(
        height=520,
        showlegend=False,
        coloraxis_showscale=False,
        margin={"r": 10, "t": 10, "l": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(bar_figure, width="stretch", config={"displaylogo": False})

with right:
    st.subheader("Atenção básica × capacidade hospitalar")
    scatter = px.scatter(
        filtered,
        x="ubs_por_10k",
        y="hospitais_por_100k",
        size="populacao",
        color="regiao",
        hover_name="municipio",
        hover_data={"uf": True, "populacao": ":,.0f", "indice_lacuna": ":.2f"},
        size_max=38,
        labels={
            "ubs_por_10k": "UBS por 10 mil habitantes",
            "hospitais_por_100k": "Hospitais por 100 mil habitantes",
            "regiao": "Região",
            "uf": "UF",
            "populacao": "População",
            "indice_lacuna": "Índice de lacuna",
        },
    )
    scatter.update_layout(
        height=520,
        margin={"r": 10, "t": 10, "l": 10, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})

st.subheader("Dados municipais")
display_columns = {
    "municipio": "Município",
    "uf": "UF",
    "regiao": "Região",
    "populacao": "População",
    "ubs": "UBS",
    "hospitais": "Hospitais",
    "centros_cirurgicos": "Centros cirúrgicos",
    "centros_obstetricos": "Centros obstétricos",
    "ubs_por_10k": "UBS / 10 mil",
    "hospitais_por_100k": "Hospitais / 100 mil",
    "indice_lacuna": "Índice de lacuna",
    "prioridade_exploratoria": "Faixa exploratória",
    "distancia_hospital_proxy_km": "Distância proxy hospitalar (km)",
    "sensibilidade_amplitude_indice": "Amplitude entre cenários",
    "estabilidade_ranking": "Estabilidade do ranking (0–100)",
}
table = filtered[list(display_columns)].rename(columns=display_columns)
st.dataframe(table, width="stretch", hide_index=True, height=420)
st.download_button(
    "Baixar recorte em CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="saude_brasil_insights_recorte.csv",
    mime="text/csv",
)

with st.expander("Análise de sensibilidade dos pesos"):
    st.markdown(
        "A amplitude mostra quanto o índice municipal varia entre seis combinações de pesos. "
        "A estabilidade resume a variação da posição no ranking: valores próximos de 100 "
        "indicam menor dependência dos pesos testados."
    )
    sensitivity = filtered.nlargest(20, "sensibilidade_amplitude_indice")[
        [
            "municipio",
            "uf",
            "indice_lacuna",
            "sensibilidade_amplitude_indice",
            "sensibilidade_desvio_indice",
            "estabilidade_ranking",
        ]
    ]
    st.dataframe(sensitivity, width="stretch", hide_index=True)

with st.expander("Metodologia, qualidade e limitações"):
    st.markdown(
        """
        - O índice usa o complemento do percentil nacional ponderado: **65% UBS** e **35%
          estabelecimentos hospitalares ativos**. Ele mede posição relativa, não suficiência
          clínica.
        - UBS e hospitais são associados pelo código municipal DATASUS de seis dígitos.
        - Municípios pequenos podem depender adequadamente de redes regionais; por isso, ausência
          local de hospital não equivale automaticamente a desassistência.
        - Cadastro não prova funcionamento, disponibilidade em tempo real, qualidade ou acesso.
        - A distância é um proxy geodésico entre centros de caixas envolventes municipais; não
          considera estradas, barreiras, referência regional, transporte ou tempo de viagem.
        """
    )
    st.json(metadata["quality"], expanded=False)
    st.markdown("**Fontes oficiais**")
    for source, url in metadata["sources"].items():
        st.markdown(f"- [{source}]({url})")
