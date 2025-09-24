import os
import sys
import yaml
import pyodbc
import pandas as pd
from pathlib import Path

# ---------------- Função para carregar dados do YAML (Etapa 1) ----------------
def carregar_yaml(guid):
    caminho = os.path.join("Historico", f"{guid}.yaml")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"❌ Arquivo {caminho} não encontrado. Rode a Etapa 1 antes.")
    
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ---------------- Conectar ao Dremio usando Docker Secrets ----------------
def conectar_dremio():
    """
    Conecta ao Dremio lendo credenciais de Docker Secrets
    Secrets esperados: dremio-host, dremio-port, dremio-user, dremio-password
    """
    secrets_path = Path('/run/secrets')
    
    def ler_secret(nome_secret, valor_default=None):
        """Lê um secret ou usa valor padrão/fallback"""
        secret_file = secrets_path / nome_secret
        
        if secret_file.exists():
            with open(secret_file, 'r') as f:
                return f.read().strip()
        elif valor_default is not None:
            return valor_default
        else:
            raise FileNotFoundError(f"Secret {nome_secret} não encontrado e nenhum valor padrão definido")
    
    try:
        # Lê secrets com fallbacks
        host = ler_secret('dremio-host')
        port = ler_secret('dremio-port', '31010')  # Porta padrão
        user = ler_secret('dremio-user')
        password = ler_secret('dremio-password')
        
        # Construção da string de conexão
        conn_str = (
            "Driver={Dremio ODBC Driver 64-bit};"
            "ConnectionType=Direct;"
            f"HOST={host};"
            f"PORT={port};"
            f"UID={user};"
            f"PWD={password};"
            "AuthenticationType=Plain;"
            "UseUnicode=Yes;"
            "CharacterSet=UTF-8;"
        )
        
        print(f"🔗 Conectando ao Dremio em {host}:{port}...")
        connection = pyodbc.connect(conn_str, autocommit=True, timeout=30)
        print("✅ Conexão estabelecida com sucesso")
        return connection
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao Dremio: {e}")
        raise

# ---------------- Rodar query e salvar CSV ----------------
def gerar_amostra(guid, tabela):
    """
    Gera amostra aleatória da tabela e salva como CSV
    """
    conn = None
    try:
        conn = conectar_dremio()
        
        # Query com amostragem aleatória
        query = f'SELECT * FROM "{tabela}" ORDER BY RANDOM() LIMIT 200'
        print(f"📊 Executando query: {query}")
        
        df = pd.read_sql(query, conn)
        print(f"✅ Query executada. {len(df)} registros recuperados")
        
        # Salvar CSV
        pasta = "Historico"
        os.makedirs(pasta, exist_ok=True)
        caminho_csv = os.path.join(pasta, f"{guid}_amostra.csv")
        df.to_csv(caminho_csv, index=False, encoding="utf-8")
        
        # Estatísticas básicas
        print(f"📈 Estatísticas da amostra:")
        print(f"   - Total de registros: {len(df)}")
        print(f"   - Colunas: {len(df.columns)}")
        print(f"   - Tamanho do arquivo: {os.path.getsize(caminho_csv)} bytes")
        print(f"💾 Amostra salva em: {caminho_csv}")
        
        return caminho_csv
        
    except pyodbc.Error as e:
        print(f"❌ Erro de banco de dados: {e}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("🔌 Conexão fechada")

# ---------------- Validação de Secrets ----------------
def validar_secrets():
    """
    Valida se os secrets necessários estão presentes
    """
    secrets_obrigatorios = ['dremio-host', 'dremio-user', 'dremio-password']
    secrets_path = Path('/run/secrets')
    
    print("🔍 Validando Docker Secrets...")
    
    for secret in secrets_obrigatorios:
        secret_file = secrets_path / secret
        if not secret_file.exists():
            print(f"⚠️  Aviso: Secret {secret} não encontrado em {secret_file}")
        else:
            print(f"✅ Secret {secret} encontrado")
    
    # Verifica se pelo menos os obrigatórios existem
    secrets_existentes = [s for s in secrets_obrigatorios if (secrets_path / s).exists()]
    if len(secrets_existentes) < len(secrets_obrigatorios):
        print("❌ Secrets obrigatórios faltando. Verifique a montagem dos volumes.")
        return False
    
    return True

# ---------------- Execução Principal ----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python Etapa3.py <GUID>")
        print("💡 Exemplo: python Etapa3.py 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

    guid = sys.argv[1]
    print(f"🚀 Iniciando Etapa 3 para GUID: {guid}")

    try:
        # Valida secrets antes de prosseguir
        if not validar_secrets():
            sys.exit(1)
        
        # Carrega configuração do YAML
        dados = carregar_yaml(guid)
        tabela = dados.get("dremio_table")
        
        if not tabela:
            raise ValueError("⚠️ Campo 'dremio_table' não encontrado no YAML da Etapa 1.")

        print(f"📋 Tabela alvo: {tabela}")
        
        # Gera amostra
        caminho_csv = gerar_amostra(guid, tabela)
        
        print(f"🎉 Etapa 3 concluída com sucesso!")
        print(f"📁 Arquivo gerado: {caminho_csv}")

    except FileNotFoundError as e:
        print(f"❌ Arquivo não encontrado: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro na Etapa 3: {e}")
        sys.exit(1)