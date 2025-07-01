"""
Gera observações RDF com preço simulado do Bitcoin a cada 5 s
e faz INSERT DATA no Fuseki.
"""
import os, time, random, requests
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, XSD

time.sleep(10)
EX     = Namespace("http://example.org/btc#")
SOSA   = Namespace("http://www.w3.org/ns/sosa/")
SCHEMA = Namespace("http://schema.org/")

# URL de atualização SPARQL (dataset btc)
FUSEKI_UPDATE = os.getenv("FUSEKI_UPDATE", "http://localhost:3030/btc/update")

# ---------- envia metadados estáticos (apenas 1ª execução) ----------
static = Graph()
static.bind("ex", EX); static.bind("sosa", SOSA)
static.add((EX.btcSensor, RDF.type, SOSA.Sensor))
static.add((EX.btcSensor, SOSA.observes, EX.Bitcoin))
requests.post(FUSEKI_UPDATE, data={"update": static.serialize(format="nt")})

# ---------- loop de streaming ----------
while True:
    g = Graph()
    g.bind("ex", EX); g.bind("sosa", SOSA)
    
    ts   = time.strftime('%Y-%m-%dT%H:%M:%S')
    obs  = URIRef(f"http://example.org/btc/obs/{int(time.time())}")
    val  = round(random.uniform(300000, 400000), 2)   # valor fictício em BRL

    g.add((obs, RDF.type, EX.BitcoinPriceObservation))
    g.add((obs, RDF.type, SOSA.Observation))      
    g.add((obs, SOSA.madeBySensor, EX.btcSensor))
    g.add((obs, SOSA.hasFeatureOfInterest, EX.Bitcoin))
    g.add((obs, SOSA.resultTime, Literal(ts, datatype=XSD.dateTime)))
    g.add((obs, EX.priceValue, Literal(val, datatype=XSD.float)))
    g.add((obs, EX.currency, Literal("BRL", datatype=XSD.string)))
    g.add((obs, SOSA.hasSimpleResult, Literal(val, datatype=XSD.float)))


    nt = g.serialize(format="nt")
    resp = requests.post(FUSEKI_UPDATE, data={"update": f"INSERT DATA {{ {nt} }}"}, auth=('admin', 'admin'))
    if resp.status_code != 200:
        print("ERRO →", resp.status_code, resp.text[:120])
    print(f"[{ts}] Preço simulado R$ {val}")
    time.sleep(5)
