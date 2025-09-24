import os
import sys
import yaml
import pyodbc
import pandas as pd

def carregar_yaml(guid):
    caminho = os.path.join("Historico", f"{guid}.yaml")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"❌ Arquivo {caminho} não encontrado. Rode a Etapa 1 antes.")
    
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def conectar_dremio():
    conn_str = (
        "Driver={Dremio ODBC Driver 64-bit};"
        "ConnectionType=Direct;"
        f"HOST={os.getenv('DREMIO_HOST')};"
        f"PORT={os.getenv('DREMIO_PORT', '31010')};"
        f"UID={os.getenv('DREMIO_USER')};"
        f"PWD={os.getenv('DREMIO_PASSWORD')};"
        "AuthenticationType=Plain;"
    )
    return pyodbc.connect(conn_str, autocommit=True)

def gerar_amostra(guid, tabela):
    conn = conectar_dremio()
    query = f'SELECT * FROM "{tabela}" ORDER BY RANDOM() LIMIT 200'
    df = pd.read_sql(query, conn)
    conn.close()

    pasta = "Historico"
    os.makedirs(pasta, exist_ok=True)
    caminho_csv = os.path.join(pasta, f"{guid}_amostra.csv")
    df.to_csv(caminho_csv, index=False, encoding="utf-8")

    print(f"✅ Amostra salva em {caminho_csv}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python Etapa3.py <GUID>")
        sys.exit(1)

    guid = sys.argv[1]

    try:
        dados = carregar_yaml(guid)
        tabela = dados.get("dremio_table")
        if not tabela:
            raise ValueError("⚠️ Campo 'dremio_table' não encontrado no YAML da Etapa 1.")

        gerar_amostra(guid, tabela)

    except Exception as e:
        print(f"❌ Erro na Etapa 3: {e}")
        sys.exit(1)
