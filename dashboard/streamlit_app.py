# app/streamlit_app.py
"""BTC Linked‑Data Dashboard – 5 consultas de arquivos com gráficos persistentes."""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
from SPARQLWrapper import SPARQLWrapper, JSON
from streamlit_autorefresh import st_autorefresh
from pathlib import Path

# Configuração geral
st.set_page_config(
    page_title="BTC Linked‑Data Dashboard",
    page_icon="📈",
    layout="wide"
)
FUSEKI_QUERY = os.getenv("FUSEKI_QUERY", "http://fuseki:3030/btc/query")

# Carrega consultas .rq na pasta queries/
def load_queries(folder: str) -> dict:
    qdir = Path(folder)
    queries = {}
    for path in sorted(qdir.glob("*.rq")):
        key = path.stem
        sparql = path.read_text().strip()
        # Determina tipo de gráfico pelo prefixo do arquivo
        if key.startswith("hourly_avg"):
            qtype = "bar"
        elif key.startswith("daily_high_low"):
            qtype = "area"
        elif key.startswith("spikes_7d"):
            qtype = "line_spike"
        elif key.startswith("median_last_hour"):
            qtype = "metric"
        else:
            qtype = "line"
        queries[key] = {
            "title": key.replace("_", " ").title(),
            "type": qtype,
            "sparql": sparql
        }
    return queries

QUERIES = load_queries("queries")

# Função de consulta SPARQL
@st.cache_data(ttl=20)
def run_query(query: str) -> pd.DataFrame:
    sparql = SPARQLWrapper(FUSEKI_QUERY)
    sparql.setCredentials("admin", "admin")  # ajuste se não precisar auth
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    res = sparql.query().convert()
    cols = res["head"]["vars"]
    rows = [[b.get(c, {}).get("value") for c in cols]
            for b in res["results"]["bindings"]]
    return pd.DataFrame(rows, columns=cols)

# Cabeçalho e gráfico live (auto-refresh)
st.title("📈 BTC Linked‑Data Dashboard")
st_autorefresh(interval=15000, key="live_refresh")
# Usa sempre a consulta 'latest_30' para o gráfico principal
graph_key = "latest_20"
if graph_key in QUERIES:
    live_df = run_query(QUERIES[graph_key]["sparql"])
    if not live_df.empty:
        # Formata colunas de data e valor
        live_df["hora"] = pd.to_datetime(live_df["hora"])
        live_df["valor"] = pd.to_numeric(live_df["valor"])
        fig = px.line(
            live_df.sort_values("hora"),
            x="hora", y="valor",
            title=f"Live: {QUERIES[graph_key]['title']}",
            markers=True,
            template="plotly_dark"
        )
        # Ajusta formatação do eixo X para data e hora
        fig.update_layout(
            xaxis_title="Horário",
            yaxis_title="Valor (BRL)",
            xaxis=dict(
                tickformat="%Y-%m-%d\n%H:%M:%S",
                tickangle= -45
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados no Fuseki para a consulta 'Latest 30'.")
else:
    st.error("Consulta 'latest_30.rq' não encontrada em queries/. ")

# Seletor de consulta e execução
sel_key = st.selectbox(
    "Escolha uma análise:",
    list(QUERIES.keys()),
    format_func=lambda k: QUERIES[k]["title"]
)
st.code(QUERIES[sel_key]["sparql"], language="sparql")

if st.button("Executar consulta"):
    df = run_query(QUERIES[sel_key]["sparql"])
    st.session_state["df"] = df
    st.session_state["sel"] = sel_key

# Exibição do resultado persistente
if "df" in st.session_state and "sel" in st.session_state:
    df = st.session_state["df"]
    sel = st.session_state["sel"]
    if df.empty:
        st.warning("Nenhum resultado para essa consulta.")
    else:
        # Conversões automáticas de tipo
        for c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c])
            except:
                try:
                    df[c] = pd.to_datetime(df[c])
                except:
                    pass
        st.dataframe(df, height=300, use_container_width=True)

        # Visualizações específicas
        gtype = QUERIES[sel]["type"]
        if gtype == "bar":
            fig2 = px.bar(
                df,
                x=df.columns[0], y=df.columns[1],
                title=QUERIES[sel]["title"],
                labels={df.columns[0]: "Horário", df.columns[1]: "Valor (BRL)"},
                template="plotly_white"
            )
            st.plotly_chart(fig2, use_container_width=True)

        elif gtype == "area":
            fig2 = px.area(
                df.sort_values(df.columns[0]),
                x=df.columns[0], y=df.columns[1:],
                title=QUERIES[sel]["title"],
                labels={df.columns[0]: "Data", df.columns[1]: "Valor (BRL)"},
                template="plotly_white"
            )
            fig2.update_layout(legend_title_text="Legenda")
            st.plotly_chart(fig2, use_container_width=True)

        elif gtype == "line_spike":
            fig2 = px.scatter(
                df,
                x=df.columns[0], y=df.columns[1],
                size=df.columns[1],
                color=df.columns[1],
                title=QUERIES[sel]["title"],
                labels={df.columns[0]: "Data", df.columns[1]: "% de Spike"},
                template="plotly_white",
                hover_data=df.columns
            )
            st.plotly_chart(fig2, use_container_width=True)

        elif gtype == "metric":
            val = float(df.iloc[0, 0])
            st.metric(QUERIES[sel]["title"], f"R$ {val:,.2f}")

        else:  # line padrão
            fig2 = px.line(
                df.sort_values(df.columns[0]),
                x=df.columns[0], y=df.columns[1],
                title=QUERIES[sel]["title"],
                markers=True,
                labels={df.columns[0]: "Horário", df.columns[1]: "Valor (BRL)"},
                template="plotly_white"
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Download CSV
        st.download_button(
            "⬇️ CSV",
            df.to_csv(index=False).encode(),
            file_name=f"{sel}.csv"
        )
