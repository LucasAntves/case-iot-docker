# Usa o Python no Debian 11 (Bullseye)
FROM python:3.9-slim-bullseye

# Cria pastas de manual que às vezes faltam
RUN mkdir -p /usr/share/man/man1

# Atualiza e instala o Java 11 e utilitários
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless procps && \
    rm -rf /var/lib/apt/lists/*

# Detecta a arquitetura (amd64 ou arm64) e cria um link simbólico genérico
RUN ln -s /usr/lib/jvm/java-11-openjdk-$(dpkg --print-architecture) /usr/lib/jvm/java-home

# Configura o JAVA_HOME apontando para o link genérico que criamos
ENV JAVA_HOME=/usr/lib/jvm/java-home
ENV PATH=$JAVA_HOME/bin:$PATH

# Define diretório de trabalho
WORKDIR /app

# Copia as dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY src/ ./src/

# Comando padrão
CMD ["python", "src/consumer/processamento_spark.py"]