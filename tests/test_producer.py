import unittest
import sys
import os
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.producer.sensor_producer import gerar_dado_sensor, CIDADES

class TestProducerUnit(unittest.TestCase):

    def test_campos_obrigatorios(self):
        """Verifica se o JSON gerado tem todos os campos que o Banco espera"""
        dado = gerar_dado_sensor()
        campos = ["sensor_id", "temperatura", "umidade", "data_hora", "cidade", "status"]
        for campo in campos:
            self.assertIn(campo, dado)

    def test_tipos_de_dados(self):
        """Verifica se temperatura é número e cidade é texto"""
        dado = gerar_dado_sensor()
        self.assertIsInstance(dado['temperatura'], float)
        self.assertIsInstance(dado['umidade'], float)
        self.assertIsInstance(dado['cidade'], str)

    def test_validade_cidade(self):
        """Garante que a cidade gerada está na nossa lista oficial"""
        dado = gerar_dado_sensor()
        self.assertIn(dado['cidade'], CIDADES)

    def test_formato_data(self):
        """Verifica se a data é uma string ISO válida e recente"""
        dado = gerar_dado_sensor()
        # Tenta converter a string de volta para objeto data para ver se não quebra
        try:
            data_obj = datetime.fromisoformat(dado['data_hora'])
            self.assertIsInstance(data_obj, datetime)
        except ValueError:
            self.fail("A data gerada não está no formato ISO 8601 correto!")

if __name__ == '__main__':
    unittest.main()