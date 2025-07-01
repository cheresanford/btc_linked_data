# Imagem enxuta com Python 3.11
FROM python:3.11-slim

# Argumento: URL de atualização SPARQL (definido no compose)
ARG FUSEKI_UPDATE=http://fuseki:3030/btc/update   # hostname “fuseki” vem do serviço no compose

ENV FUSEKI_UPDATE=$FUSEKI_UPDATE \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependências do sistema (curl apenas para debug opcional)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código-fonte
COPY btc_stream.py .

# Script será ponto de entrada
ENTRYPOINT ["python", "btc_stream.py"]
