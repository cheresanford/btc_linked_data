
# 📈 Bitcoin Linked Data Dashboard

Este projeto simula, armazena e visualiza dados de preços do Bitcoin como **Linked Data** utilizando as tecnologias RDF, SPARQL, Apache Jena Fuseki e Streamlit.

## 🔧 Tecnologias

- **Python** (Streamlit + RDFLib)
- **Docker** + `docker-compose`
- **Apache Jena Fuseki** como triplestore RDF
- **SPARQL** para consultas
- **Plotly** para visualização interativa de dados
- **Pandas** para manipulação dos resultados

---

## 📁 Estrutura do Projeto

```bash
.
├── docker-compose.yml
├── fuseki-data/            # Dados persistentes do Fuseki
├── generator/              # Gerador de dados RDF simulados
│   └── btc_stream.py
├── queries/                # Consultas SPARQL reutilizáveis
│   ├── latest_30.rq
│   ├── hourly_avg_24h.rq
│   ├── daily_high_low_7d.rq
│   ├── spikes_7d.rq
│   └── median_last_hour.rq
└── app/
    └── streamlit_app.py    # Painel interativo
````

---

## ▶️ Como rodar

1. **Clonar o projeto**

```bash
git clone https://github.com/seu-usuario/btc-linked-data-dashboard.git
cd btc-linked-data-dashboard
```

2. **Subir o ambiente com Docker**

```bash
docker compose up --build
```

3. **Acessar as interfaces**

* Painel interativo (Streamlit): [http://localhost:8501](http://localhost:8501)
* Fuseki Admin: [http://localhost:3030](http://localhost:3030)
  Login padrão: `admin` / `admin`

---

## 🧠 O que esse projeto faz?

### 🔄 Geração de Dados

* A cada 5 segundos, um preço fictício do Bitcoin é gerado.
* Os dados são convertidos para RDF usando o vocabulário [SOSA](https://www.w3.org/TR/vocab-ssn/) e enviados para o Fuseki via SPARQL `INSERT DATA`.

### 📊 Visualização dos Dados

O painel apresenta:

1. **Gráfico ao vivo com auto-refresh** das últimas 30 leituras.
2. **Análises interativas** baseadas em consultas SPARQL específicas:

   * Média horária das últimas 24h
   * Máximos e mínimos por dia (últimos 7 dias)
   * Spikes ≥ 5% por dia
   * Mediana na última hora

---

## 🗂 Consultas SPARQL

As consultas estão salvas em `/queries`. Cada uma tem visualização customizada no painel.

Exemplo:

```sparql
# Últimas 30 leituras
PREFIX ex:<http://example.org/btc#>
PREFIX sosa:<http://www.w3.org/ns/sosa/>
SELECT ?hora ?valor
WHERE {
  ?o a ex:BitcoinPriceObservation ;
     ex:priceValue ?valor ;
     sosa:resultTime ?hora .
}
ORDER BY DESC(?hora)
LIMIT 30
```

---

## 💾 Persistência

Os dados RDF ficam salvos no volume `fuseki-data`. Ao clonar este repositório em outro lugar, **os dados simulados não são transferidos**, pois estão apenas localmente no volume Docker. Se quiser backup, exporte via Fuseki GUI ou comandos SPARQL.

---

## 📌 Requisitos

* Docker e Docker Compose instalados
* Porta 8501 (Streamlit) e 3030 (Fuseki) livres

---

## 📚 Referências

* [W3C SOSA Ontology](https://www.w3.org/TR/vocab-ssn/)
* [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)
* [Streamlit Docs](https://docs.streamlit.io/)
* [SPARQL Tutorial](https://www.w3.org/TR/sparql11-query/)

---

## 📬 Contato

Projeto educacional desenvolvido como parte de um trabalho de Ciência da Computação.
Dúvidas ou sugestões? Entre em contato pelo GitHub Issues ou pelo email associado.

---

```

---