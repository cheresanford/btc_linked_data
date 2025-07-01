import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from SPARQLWrapper import SPARQLWrapper, JSON
from streamlit_autorefresh import st_autorefresh

###############################################################################
# Configurações iniciais
###############################################################################
st.set_page_config(
    page_title="Linked Data • Bitcoin Dashboard",
    layout="wide",
    page_icon="📈"
)

st.title("📈 Bitcoin Linked Data Dashboard")
st.caption("Streaming Linked Data › Fuseki ▸ SPARQL ▸ Streamlit")

###############################################################################
# Conexão com Fuseki
###############################################################################
FUSEKI_QUERY = os.getenv("FUSEKI_QUERY", "http://localhost:3030/btc/query")

@st.cache_data(ttl=60)
def run_query(query_str: str) -> pd.DataFrame:
    """Executa consulta SPARQL e devolve DataFrame."""
    sparql = SPARQLWrapper(FUSEKI_QUERY)
    sparql.setCredentials("admin", "admin")  # remova se Fuseki não exigir auth
    sparql.setQuery(query_str)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except Exception as exc:
        st.error(f"Erro ao consultar Fuseki: {exc}")
        return pd.DataFrame()
    vars_ = results["head"]["vars"]
    rows = [
        [binding.get(v, {}).get("value") for v in vars_]
        for binding in results["results"]["bindings"]
    ]
    return pd.DataFrame(rows, columns=vars_)

###############################################################################
# Gráfico principal (auto‑refresh)
###############################################################################
st_autorefresh(interval=15_000, key="data_refresh")  # 15 s

query_chart = """
PREFIX ex:<http://example.org/btc#>
PREFIX sosa:<http://www.w3.org/ns/sosa/>
SELECT ?hora ?valor
WHERE {
  ?o a ex:BitcoinPriceObservation ;
     ex:priceValue ?valor ;
     sosa:resultTime ?hora .
}
ORDER BY DESC(?hora)
LIMIT 50
"""

df_chart = run_query(query_chart)
if df_chart.empty:
    st.warning("Sem dados no Fuseki – verifique se o gerador está rodando.")
else:
    df_chart["hora"] = pd.to_datetime(df_chart["hora"])
    df_chart["valor"] = pd.to_numeric(df_chart["valor"])
    df_chart = df_chart.sort_values("hora")
    fig = px.line(
        df_chart,
        x="hora",
        y="valor",
        title="Variação recente do preço (últimas 50 leituras)",
        markers=True,
        template="plotly_dark"
    )
    fig.update_traces(line=dict(width=2))
    st.plotly_chart(fig, use_container_width=True)

###############################################################################
# Seletor de Query
###############################################################################
st.markdown("## 📂 Consultas SPARQL salvas")
queries_dir = "./queries"
if not os.path.exists(queries_dir):
    st.info("Pasta `queries/` não encontrada no container.")
else:
    arquivos = sorted([f for f in os.listdir(queries_dir) if f.endswith(".rq")])
    escolha = st.selectbox("Escolha uma consulta", arquivos, index=0)
    caminho = os.path.join(queries_dir, escolha)
    with open(caminho) as fp:
        query_txt = fp.read()
    st.code(query_txt, language="sparql")

    if st.button("Executar consulta"):
        df_result = run_query(query_txt)
        st.subheader("Resultado")
        st.dataframe(df_result, height=300, use_container_width=True)
        if not df_result.empty:
            csv = df_result.to_csv(index=False).encode()
            st.download_button("⬇️ Baixar CSV", csv, file_name=f"{escolha}.csv", mime="text/csv")