import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

# --- CONFIGURAÇÕES ---
# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = "sensores-iot"

DB_HOST = os.getenv('POSTGRES_HOST', 'postgres-iot')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'iot_db')
DB_USER = os.getenv('POSTGRES_USER', 'admin')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_TABLE = "sensores"

if not DB_PASSWORD:
    raise ValueError("A senha do banco de dados (POSTGRES_PASSWORD) não foi definida nas variáveis de ambiente!")

# URL da conexão JDBC
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

def salvar_no_postgres(df, batch_id):
    print(f"Salvando Batch {batch_id} no Banco de Dados...")
    df.write \
        .format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", DB_TABLE) \
        .option("user", DB_USER) \
        .option("password", DB_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
        
    print(f"Batch {batch_id} salvo com sucesso!")

def main():
    
    print(f"Conectando ao Kafka em: {KAFKA_BOOTSTRAP_SERVERS}")

    # 1. Iniciar Spark Session com Driver do Kafka E do Postgres
    spark = (SparkSession.builder
        .appName("IoT Sensor Consumer")
        #driver do Postgres aqui na lista de pacotes
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0")
        .getOrCreate())

    spark.sparkContext.setLogLevel("WARN")

    # 2. Schema
    schema = StructType([
        StructField("sensor_id", IntegerType(), True),
        StructField("temperatura", DoubleType(), True),
        StructField("umidade", DoubleType(), True),
        StructField("data_hora", TimestampType(), True),
        StructField("cidade", StringType(), True),
        StructField("status", StringType(), True)
    ])

    # 3. Ler do Kafka
    df_kafka = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # 4. Transformar JSON em Colunas
    df_transformado = df_kafka.selectExpr("CAST(value AS STRING)") \
        .select(from_json(col("value"), schema).alias("dados")) \
        .select("dados.*")

    # 5. Escrever no Postgres (Usando foreachBatch)
    print("Iniciando streaming para o PostgreSQL...")
    
    query = df_transformado.writeStream \
        .foreachBatch(salvar_no_postgres) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()