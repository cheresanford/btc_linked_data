# app/streamlit_app.py
"""BTC Linked‑Data Dashboard – 5 consultas com gráficos persistentes."""

import os, pandas as pd, streamlit as st, plotly.express as px
from SPARQLWrapper import SPARQLWrapper, JSON
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BTC Linked‑Data Dashboard", page_icon="📈", layout="wide")
FUSEKI_QUERY = os.getenv("FUSEKI_QUERY", "http://fuseki:3030/btc/query")

###############################################################################
# Função de consulta                                                         
###############################################################################
@st.cache_data(ttl=20)
def run_query(query: str) -> pd.DataFrame:
    sparql = SPARQLWrapper(FUSEKI_QUERY)
    sparql.setCredentials("admin", "admin")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    res = sparql.query().convert()
    cols = res["head"]["vars"]
    rows = [[b.get(c, {}).get("value") for c in cols] for b in res["results"]["bindings"]]
    return pd.DataFrame(rows, columns=cols)

###############################################################################
# Consultas fixas
###############################################################################
QUERIES = {
    "latest_30": {"title": "📊 Últimas 30 leituras", "type": "line", "sparql": """
PREFIX ex:<http://example.org/btc#> PREFIX sosa:<http://www.w3.org/ns/sosa/>
SELECT ?hora ?valor WHERE { ?o a ex:BitcoinPriceObservation ; ex:priceValue ?valor ; sosa:resultTime ?hora . }
ORDER BY DESC(?hora) LIMIT 30"""},
    "hourly_avg_24h": {"title": "⏲️ Média horária (24h)", "type": "bar", "sparql": """
PREFIX ex:<http://example.org/btc#> PREFIX sosa:<http://www.w3.org/ns/sosa/> PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
SELECT ?hora (AVG(?v) AS ?media) WHERE { ?o a ex:BitcoinPriceObservation ; ex:priceValue ?v ; sosa:resultTime ?t .
 FILTER(?t>=NOW()-"P1D"^^xsd:duration) BIND(SUBSTR(STR(?t),1,13) AS ?hora)} GROUP BY ?hora ORDER BY ?hora"""},
    "daily_high_low_7d": {"title": "📈📉 Máx & mín (7d)", "type": "area", "sparql": """
PREFIX ex:<http://example.org/btc#> PREFIX sosa:<http://www.w3.org/ns/sosa/> PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
SELECT ?dia (MAX(?v) AS ?max) (MIN(?v) AS ?min) WHERE { ?o a ex:BitcoinPriceObservation ; ex:priceValue ?v ; sosa:resultTime ?t .
 FILTER(?t>=NOW()-"P7D"^^xsd:duration) BIND(SUBSTR(STR(?t),1,10) AS ?dia)} GROUP BY ?dia ORDER BY ?dia"""},
    "spikes_7d": {"title": "🚀 Spikes ≥5 % (7d)", "type": "line_spike", "sparql": """
PREFIX ex:<http://example.org/btc#> PREFIX sosa:<http://www.w3.org/ns/sosa/> PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
SELECT ?dia (COUNT(*) AS ?num) WHERE { ?a a ex:BitcoinPriceObservation ; ex:priceValue ?pv ; sosa:resultTime ?pt .
 ?b a ex:BitcoinPriceObservation ; ex:priceValue ?cv ; sosa:resultTime ?ct .
 FILTER(?ct>?pt && ?ct<=?pt+"PT1M"^^xsd:duration && ?cv>=?pv*1.05) FILTER(?ct>=NOW()-"P7D"^^xsd:duration)
 BIND(SUBSTR(STR(?ct),1,10) AS ?dia)} GROUP BY ?dia ORDER BY ?dia"""},
    "median_last_hour": {"title": "🧮 Mediana última hora", "type": "metric", "sparql": """
PREFIX ex:<http://example.org/btc#> PREFIX sosa:<http://www.w3.org/ns/sosa/> PREFIX xsd:<http://www.w3.org/2001/XMLSchema#>
SELECT (MEDIAN(?v) AS ?mediana) WHERE { ?o a ex:BitcoinPriceObservation ; ex:priceValue ?v ; sosa:resultTime ?t .
 FILTER(?t>=NOW()-"PT1H"^^xsd:duration)}"""}
}

###############################################################################
# Gráfico live auto‑refresh (latest_30)
###############################################################################
st.title("📈 Bitcoin – Dashboard Linked‑Data")
st_autorefresh(interval=15000, key="refresh")
live_df = run_query(QUERIES["latest_30"]["sparql"])
if not live_df.empty:
    live_df["hora"] = pd.to_datetime(live_df["hora"])
    live_df["valor"] = pd.to_numeric(live_df["valor"])
    st.plotly_chart(px.line(live_df.sort_values("hora"), x="hora", y="valor",
                            title="Últimas 30 leituras (auto‑refresh)", markers=True,
                            template="plotly_dark"), use_container_width=True)
else:
    st.info("Sem dados no Fuseki.")

###############################################################################
# Seletor de consulta e execução (resultado persiste no session_state)
###############################################################################
sel_key = st.selectbox("Escolha uma análise:", list(QUERIES.keys()),
                      format_func=lambda k: QUERIES[k]["title"])
query_sql = QUERIES[sel_key]["sparql"]
st.code(query_sql, language="sparql")

if st.button("Executar consulta"):
    df = run_query(query_sql)
    st.session_state["df"]   = df
    st.session_state["sel"]  = sel_key

# ---------- Mostrar resultado salvo (sobrevive ao refresh) ------------------
if "df" in st.session_state:
    df = st.session_state["df"]
    sel = st.session_state["sel"]
    if df.empty:
        st.warning("Nenhum resultado.")
    else:
        # Conversões genéricas
        for c in df.columns:
            try: df[c] = pd.to_numeric(df[c])
            except: 
                try: df[c] = pd.to_datetime(df[c])
                except: pass
        st.dataframe(df, height=300, use_container_width=True)

        kind = QUERIES[sel]["type"]
        if kind == "bar":
            fig = px.bar(df, x="hora", y="media", template="plotly_white",
                         title="Média hora‑a‑hora (24h)")
            st.plotly_chart(fig, use_container_width=True)

        elif kind == "area":
            fig = px.area(df.sort_values("dia"), x="dia", y=["max","min"],
                          template="plotly_white", title="Faixa diária de preços (7 dias)")
            st.plotly_chart(fig, use_container_width=True)

        elif kind == "line_spike":
            fig = px.line(df, x="dia", y="num", markers=True,
                          template="plotly_white", title="Spikes (≥5 %) por dia")
            st.plotly_chart(fig, use_container_width=True)

        elif kind == "metric":
            st.metric("Mediana últimos 60 min", f"R$ {float(df['mediana'].iloc[0]):,.2f}")

        else:  # line padrão latest_30
            fig = px.line(df.sort_values("hora"), x="hora", y="valor",
                          markers=True, template="plotly_white",
                          title="Últimas 30 leituras")
            st.plotly_chart(fig, use_container_width=True)
        st.download_button("⬇️ CSV", df.to_csv(index=False).encode(),
                           file_name=f"{sel}.csv")
