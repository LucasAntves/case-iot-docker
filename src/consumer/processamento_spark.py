import os
import sys
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType

# --- CONFIGURAÇÃO DE LOGS ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] SparkConsumer: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = "sensores-iot"

# Postgres
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres-iot')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'iot_db')
DB_USER = os.getenv('POSTGRES_USER', 'admin')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB_TABLE = "sensores"

if not DB_PASSWORD:
    logger.critical("A senha do banco de dados (POSTGRES_PASSWORD) não foi definida!")
    raise ValueError("Variável de ambiente POSTGRES_PASSWORD obrigatória.")

JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

def salvar_no_postgres(df, batch_id):
    """Função chamada para cada micro-batch."""
    try:
        count = df.count()
        if count > 0:
            logger.info(f"Processando Batch {batch_id} com {count} registros...")
            
            df.write \
                .format("jdbc") \
                .option("url", JDBC_URL) \
                .option("dbtable", DB_TABLE) \
                .option("user", DB_USER) \
                .option("password", DB_PASSWORD) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"Batch {batch_id} salvo com sucesso no PostgreSQL!")
        else:
            logger.info(f"Batch {batch_id} vazio. Nada a salvar.")
            
    except Exception as e:
        logger.error(f"Erro ao salvar Batch {batch_id} no banco: {e}", exc_info=True)

def main():
    logger.info(f"Iniciando conexão Spark. Kafka: {KAFKA_BOOTSTRAP_SERVERS} | Postgres: {DB_HOST}")

    spark = (SparkSession.builder
        .appName("IoT Sensor Consumer")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0")
        .getOrCreate())

    spark.sparkContext.setLogLevel("WARN")
    logger.info("Spark Session criada com sucesso!")

    schema = StructType([
        StructField("sensor_id", IntegerType(), True),
        StructField("temperatura", DoubleType(), True),
        StructField("umidade", DoubleType(), True),
        StructField("data_hora", TimestampType(), True),
        StructField("cidade", StringType(), True),
        StructField("status", StringType(), True)
    ])

    try:
        df_kafka = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
            .option("subscribe", KAFKA_TOPIC) \
            .option("startingOffsets", "latest") \
            .load()

        df_transformado = df_kafka.selectExpr("CAST(value AS STRING)") \
            .select(from_json(col("value"), schema).alias("dados")) \
            .select("dados.*")

        logger.info("Iniciando streaming writer...")
        
        query = df_transformado.writeStream \
            .foreachBatch(salvar_no_postgres) \
            .start()

        query.awaitTermination()
        
    except Exception as e:
        logger.critical(f"O Consumidor Spark falhou e vai parar: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()