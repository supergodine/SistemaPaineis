import unittest
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class TestGerarGrafico(unittest.TestCase):

    def gerar_grafico(self, df, titulo, tipo):
        """Gera um gráfico com base no DataFrame e retorna sua imagem codificada em Base64."""
        plt.figure(figsize=(10, 6))

        try:
            tipo = tipo.lower()
            #verificando se existe apenas uma coluna
            if len(df.columns) == 1:
                if tipo in ['barra', 'barras']:
                    plt.bar(range(len(df.iloc[:,0])), df.iloc[:, 0])
                elif tipo == 'linha':
                    plt.plot(range(len(df.iloc[:,0])), df.iloc[:, 0])
                elif tipo == 'pizza':
                    plt.pie(df.iloc[:, 0], labels=range(len(df.iloc[:,0])), autopct='%1.1f%%')
                else:
                    return None  # Retorna None se o tipo for inválido
            else:
                if tipo in ['barra', 'barras']:
                    plt.bar(df.iloc[:, 0], df.iloc[:, 1])
                elif tipo == 'linha':
                    plt.plot(df.iloc[:, 0], df.iloc[:, 1])
                elif tipo == 'pizza':
                    plt.pie(df.iloc[:, 1], labels=df.iloc[:, 0], autopct='%1.1f%%')
                else:
                    return None  # Retorna None se o tipo for inválido

            plt.title(titulo)
            plt.xlabel(df.columns[0])
            if len(df.columns) != 1:
                plt.ylabel(df.columns[1])
            plt.tight_layout()

            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plt.close()

            return base64.b64encode(buffer.getvalue()).decode('utf-8')

        except Exception as e:
            print(f"Erro ao gerar gráfico: {e}")
            return None

    def test_gerar_grafico_barra(self):
        """Testa a geração de um gráfico de barras."""
        data = {'Categoria': ['A', 'B', 'C'], 'Valor': [10, 20, 15]}
        df = pd.DataFrame(data)
        image_base64 = self.gerar_grafico(df, "Gráfico de Barras", "barra")
        self.assertIsNotNone(image_base64)
        self.assertIsInstance(image_base64, str)

    def test_gerar_grafico_linha(self):
        """Testa a geração de um gráfico de linha."""
        data = {'Tempo': [1, 2, 3, 4], 'Resultado': [5, 8, 6, 9]}
        df = pd.DataFrame(data)
        image_base64 = self.gerar_grafico(df, "Gráfico de Linha", "linha")
        self.assertIsNotNone(image_base64)
        self.assertIsInstance(image_base64, str)

    def test_gerar_grafico_pizza(self):
        """Testa a geração de um gráfico de pizza."""
        data = {'Fatia': ['Um', 'Dois', 'Três'], 'Percentual': [30, 40, 30]}
        df = pd.DataFrame(data)
        image_base64 = self.gerar_grafico(df, "Gráfico de Pizza", "pizza")
        self.assertIsNotNone(image_base64)
        self.assertIsInstance(image_base64, str)
    
    def test_tipo_grafico_invalido(self):
        """Testa a geração com um tipo de gráfico inválido."""
        data = {'x': [1, 2, 3], 'y': [4, 5, 6]}
        df = pd.DataFrame(data)
        image_base64 = self.gerar_grafico(df, "Gráfico Inválido", "tipo_invalido")
        self.assertIsNone(image_base64)

    def test_df_vazio(self):
        """Testa a geração com um DataFrame vazio."""
        df = pd.DataFrame()
        image_base64 = self.gerar_grafico(df, "Gráfico Inválido", "pizza")
        self.assertIsNone(image_base64)

if __name__ == '__main__':
    unittest.main()
