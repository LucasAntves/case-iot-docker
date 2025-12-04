import unittest
import json
import time
import uuid
from kafka import KafkaProducer, KafkaConsumer

# Configurações do teste
TOPICO_TESTE = 'sensores-iot'
SERVER = 'localhost:9092'

class TestKafkaIntegration(unittest.TestCase):

    def setUp(self):
        """Prepara o Producer antes do teste"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[SERVER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
        except:
            self.skipTest("Kafka não está acessível.")

    def test_envio_e_recebimento(self):
        """
        1. Conecta o Consumidor.
        2. Envia a mensagem.
        3. Verifica se chegou.
        """
        # ID único para garantir que não vamos ler mensagem velha de outro teste
        id_teste = str(uuid.uuid4())
        
        # 1. Cria o Consumidor (Ligar o rádio antes)
        consumer = KafkaConsumer(
            TOPICO_TESTE,
            bootstrap_servers=[SERVER],
            auto_offset_reset='latest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=5000  # Espera no máximo 5 segundos
        )
        
        # Força uma leitura "falsa" para garantir que ele conectou e pegou o final da fila
        consumer.poll(timeout_ms=1000) 

        print(f"\n[Test] Consumidor conectado. Enviando ID: {id_teste}...")

        # 2. Envia mensagem de teste
        mensagem_teste = {"sensor_id": 999999, "uuid_teste": id_teste, "status": "TESTE"}
        self.producer.send(TOPICO_TESTE, value=mensagem_teste)
        self.producer.flush() # Garante que saiu da máquina

        # 3. Procura a mensagem
        encontrou = False
        print("[Test] Procurando mensagem no Kafka...")
        
        for msg in consumer:
            dado = msg.value
            # Verifica se é a mensagem EXATA que mandamos agora (pelo UUID)
            if dado.get("uuid_teste") == id_teste:
                encontrou = True
                print("Mensagem de teste encontrada e validada!")
                break
        
        consumer.close()
        
        self.assertTrue(encontrou, "A mensagem foi enviada mas o Consumidor não a viu (Timeout).")

    def tearDown(self):
        if hasattr(self, 'producer'):
            self.producer.close()

if __name__ == '__main__':
    unittest.main()