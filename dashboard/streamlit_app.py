# app/streamlit_app.py
"""BTC Linked-Data Dashboard – consultas SPARQL com gráficos persistentes."""

import os
import re
import pandas as pd
import streamlit as st
import plotly.express as px
from SPARQLWrapper import SPARQLWrapper, JSON
from streamlit_autorefresh import st_autorefresh
from pathlib import Path

###############################################################################
# Configuração geral
###############################################################################
st.set_page_config(
    page_title="BTC Linked-Data Dashboard",
    page_icon="📈",
    layout="wide"
)
FUSEKI_QUERY = os.getenv("FUSEKI_QUERY", "http://fuseki:3030/btc/query")

###############################################################################
# Funções auxiliares
###############################################################################
def load_queries(folder: str) -> dict:
    """Lê todos os arquivos .rq em 'folder' e devolve dicionário de metadados."""
    qdir = Path(folder)
    queries = {}
    for path in sorted(qdir.glob("*.rq")):
        key = path.stem
        sparql = path.read_text().strip()

        # Determina tipo de visualização ao exibir
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
            "type":  qtype,
            "sparql": sparql,
        }
    return queries


def normalize_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converte colunas que parecem conter datas/horários:
    • ISO / xsd:dateTime
    • epoch em ns, ms ou s
    """
    date_like = re.compile(r"(hora|dia|data|timestamp)", re.I)

    for col in df.columns:
        if not date_like.search(col):
            continue  # pula se nome não sugerir data/hora

        # 1) tenta ISO / xsd:dateTime
        converted = pd.to_datetime(df[col], errors="coerce")

        # 2) se ainda restarem NaT, tenta epoch numérico
        if converted.isna().any():
            nums = pd.to_numeric(df[col], errors="coerce").fillna(-1).astype("int64")

            if (nums.abs() > 1e14).any():              # nanossegundos
                converted = pd.to_datetime(nums, unit="ns", errors="coerce")
            elif (nums.abs() > 1e11).any():            # milissegundos
                converted = pd.to_datetime(nums, unit="ms", errors="coerce")
            else:                                      # segundos
                converted = pd.to_datetime(nums, unit="s", errors="coerce")

        if not converted.isna().all():
            df[col] = converted

    return df


@st.cache_data(ttl=20)
def run_query(query: str) -> pd.DataFrame:
    """Executa a consulta SPARQL e devolve DataFrame normalizado."""
    sparql = SPARQLWrapper(FUSEKI_QUERY)
    sparql.setCredentials("admin", "admin")  # remova se não precisar auth
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)

    res = sparql.query().convert()
    cols = res["head"]["vars"]
    rows = [[b.get(c, {}).get("value") for c in cols]
            for b in res["results"]["bindings"]]

    df = pd.DataFrame(rows, columns=cols)
    df = normalize_datetime_columns(df)

    return df


###############################################################################
# Carrega consultas e cabeçalho
###############################################################################
QUERIES = load_queries("queries")

st.title("📈 BTC Linked-Data Dashboard")
st.caption("Streaming Linked-Data › Fuseki ▸ SPARQL ▸ Streamlit")

###############################################################################
# Gráfico live (auto-refresh) – usa always 'latest_20.rq'
###############################################################################

graph_key = "latest_20"
if graph_key in QUERIES:
    live_df = run_query(QUERIES[graph_key]["sparql"])
    if not live_df.empty:
        live_df["valor"] = pd.to_numeric(live_df["valor"])
        fig_live = px.line(
            live_df.sort_values("hora"),
            x="hora",
            y="valor",
            title=f"Live: {QUERIES[graph_key]['title']}",
            markers=True,
            template="plotly_dark"
        )
        fig_live.update_layout(
            xaxis_title="Horário",
            yaxis_title="Valor (BRL)",
            xaxis=dict(tickformat="%Y-%m-%d\n%H:%M:%S", tickangle=-45)
        )
        st.plotly_chart(fig_live, use_container_width=True)
    else:
        st.info("Sem dados no Fuseki para a consulta 'latest_20'.")
else:
    st.error("Arquivo 'latest_20.rq' não encontrado em queries/.")

###############################################################################
# Seletor de consulta e execução manual
###############################################################################
sel_key = st.selectbox(
    "Escolha uma análise:",
    list(QUERIES.keys()),
    format_func=lambda k: QUERIES[k]["title"]
)
st.code(QUERIES[sel_key]["sparql"], language="sparql")

if st.button("Executar consulta"):
    st.session_state["df"]  = run_query(QUERIES[sel_key]["sparql"])
    st.session_state["sel"] = sel_key

###############################################################################
# Exibição do resultado persistente
###############################################################################
if "df" in st.session_state and "sel" in st.session_state:
    df  = st.session_state["df"]
    sel = st.session_state["sel"]

    if df.empty:
        st.warning("Nenhum resultado para essa consulta.")
    else:
        st.dataframe(df, height=300, use_container_width=True)

        gtype = QUERIES[sel]["type"]

        if gtype == "bar":
            fig = px.bar(
                df,
                x=df.columns[0],
                y=df.columns[1],
                title=QUERIES[sel]["title"],
                template="plotly_white",
                labels={df.columns[0]: "Horário", df.columns[1]: "Valor (BRL)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        elif gtype == "area":
            fig = px.area(
                df.sort_values(df.columns[0]),
                x=df.columns[0],
                y=df.columns[1:],
                title=QUERIES[sel]["title"],
                template="plotly_white",
                labels={df.columns[0]: "Data"}
            )
            fig.update_layout(legend_title_text="Legenda")
            st.plotly_chart(fig, use_container_width=True)

        elif gtype == "line_spike":
            fig = px.scatter(
                df,
                x=df.columns[0],
                y=df.columns[1],
                size=df.columns[1],
                color=df.columns[1],
                title=QUERIES[sel]["title"],
                template="plotly_white",
                hover_data=df.columns,
                labels={df.columns[0]: "Data", df.columns[1]: "% Spike"}
            )
            st.plotly_chart(fig, use_container_width=True)

        elif gtype == "metric":
            val = float(df.iloc[0, 0])
            st.metric(QUERIES[sel]["title"], f"R$ {val:,.2f}")

        else:  # linha padrão
            fig = px.line(
                df.sort_values(df.columns[0]),
                x=df.columns[0],
                y=df.columns[1],
                title=QUERIES[sel]["title"],
                markers=True,
                template="plotly_white",
                labels={df.columns[0]: "Horário", df.columns[1]: "Valor (BRL)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Download
        st.download_button(
            "⬇️ CSV",
            df.to_csv(index=False).encode(),
            file_name=f"{sel}.csv"
        )
