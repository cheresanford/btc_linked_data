FROM python:3.11-slim
WORKDIR /app
COPY streamlit_app.py .
RUN pip install --no-cache-dir streamlit pandas plotly SPARQLWrapper streamlit-autorefresh
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
