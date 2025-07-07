import requests
import time
from datetime import datetime, timezone


from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
from uuid import uuid4

FUSEKI_ENDPOINT = "http://fuseki:3030/btc"
HEADERS = {
    "User-Agent": "btc-dashboard-tcc/1.0"
}
NS = Namespace("http://example.org/btc#")
SOSA = Namespace("http://www.w3.org/ns/sosa/")

def get_latest_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "brl"
    }
    r = requests.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    return r.json()["bitcoin"]["brl"]

def post_price_to_fuseki(price: float, timestamp: str):
    g = Graph()
    obs_uri = URIRef(f"{NS}obs-{uuid4()}")

    g.add((obs_uri, RDF.type, NS.BitcoinPriceObservation))
    g.add((obs_uri, NS.priceValue, Literal(price, datatype=XSD.float)))
    g.add((obs_uri, SOSA.resultTime, Literal(timestamp, datatype=XSD.dateTime)))

    data = g.serialize(format="nt")
    r = requests.post(f"{FUSEKI_ENDPOINT}/data", data=data,
                      headers={"Content-Type": "application/n-triples"},
                      auth=("admin", "admin"))
    r.raise_for_status()

if __name__ == "__main__":
    print("Iniciando coleta de preços em tempo real...")

    while True:
        try:
            price = get_latest_btc_price()
            timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            print(f"[{timestamp}] BTC = R$ {price:,.2f}")
            post_price_to_fuseki(price, timestamp)
        except Exception as e:
            print(f"Erro ao processar: {e}")

        time.sleep(20)  # espera 20 segundos para a próxima coleta
