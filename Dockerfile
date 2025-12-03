# Usa o Python no Debian 11 (Bullseye) estável e tem o Java 11
FROM python:3.9-slim-bullseye

# Cria pastas de manual que às vezes faltam no slim e causam erro no Java
RUN mkdir -p /usr/share/man/man1

# Atualiza e instala o Java 11 e procps (necessário para o Spark)
RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless procps && \
    rm -rf /var/lib/apt/lists/*

# Configura o JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Define diretório de trabalho
WORKDIR /app

# Copia as dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY src/ ./src/

# Comando para iniciar consumer
CMD ["python", "src/consumer/processamento_spark.py"]