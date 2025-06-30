# Requisitos de host
git  # versionamento
docker & docker-compose  # facilitar instalação
python >=3.10  # geração de dados

# 1. clone o projeto
git clone https://github.com/<seu-usuario>/btc-stream-linked-data.git
cd btc-stream-linked-data

# 2. crie venv
python -m venv .venv
source .venv/bin/activate
pip install rdflib requests tqdm
