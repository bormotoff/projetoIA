import os
import sys
import yaml
import requests
from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions
from msal import PublicClientApplication, TokenCache
import json
from pathlib import Path
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

# ---------------- Carregar Configurações do Arquivo Purview ----------------
def carregar_configuracoes():
    """Carrega as configurações do arquivo Purview na pasta Credenciais"""
    credenciais_path = Path("Credenciais") / "Purview"
    
    if not credenciais_path.exists():
        raise FileNotFoundError(f"❌ Arquivo de configurações não encontrado: {credenciais_path}")
    
    configuracoes = {}
    with open(credenciais_path, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith('#') and '=' in linha:
                chave, valor = linha.split('=', 1)
                configuracoes[chave.strip()] = valor.strip().strip('"\'')
    
    # Validar configurações obrigatórias
    obrigatorias = ['Ternant_ID', 'Purview_account_name', 'Scope']
    for obrigatoria in obrigatorias:
        if obrigatoria not in configuracoes:
            raise ValueError(f"❌ Configuração obrigatória não encontrada: {obrigatoria}")
    
    return configuracoes

# ---------------- Cache de Token Personalizado ----------------
class CustomTokenCache:
    """Cache personalizado para tokens usando arquivo JSON"""
    
    def __init__(self, cache_file="token_cache.json"):
        self.cache_file = cache_file
        self.cache = self._carregar_cache()
    
    def _carregar_cache(self):
        """Carrega o cache do arquivo"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _salvar_cache(self):
        """Salva o cache no arquivo"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def encontrar_token(self, scope, tenant_id):
        """Procura por token válido no cache"""
        cache_key = f"{tenant_id}_{scope}"
        
        if cache_key in self.cache:
            token_data = self.cache[cache_key]
            # Verificar se o token ainda é válido (considerando expiração)
            if self._token_valido(token_data):
                return token_data['access_token']
        return None
    
    def salvar_token(self, scope, tenant_id, token_data):
        """Salva token no cache"""
        cache_key = f"{tenant_id}_{scope}"
        self.cache[cache_key] = {
            'access_token': token_data.token,
            'expires_on': token_data.expires_on,
            'token_type': token_data.token_type
        }
        self._salvar_cache()
    
    def _token_valido(self, token_data):
        """Verifica se o token ainda é válido (com margem de segurança de 5 minutos)"""
        from time import time
        return token_data.get('expires_on', 0) > (time() + 300)

# ---------------- Autenticação com Cache e Cookies ----------------
def get_access_token(configuracoes):
    """
    Usa InteractiveBrowserCredential com cache de token e cookies
    Tenta usar cache primeiro, só abre navegador se necessário
    """
    tenant_id = configuracoes['Ternant_ID']
    scope = configuracoes['Scope']
    
    # Inicializar cache personalizado
    cache = CustomTokenCache()
    
    # Tentar obter token do cache primeiro
    token = cache.encontrar_token(scope, tenant_id)
    if token:
        print("✅ Token recuperado do cache")
        return token
    
    print("🔐 Nenhum token válido encontrado no cache. Iniciando autenticação interativa...")
    
    # Configurar opções de persistência de cache
    cache_options = TokenCachePersistenceOptions(name="purview_cache")
    
    # Criar credential com cache persistente
    credential = InteractiveBrowserCredential(
        tenant_id=tenant_id,
        cache_persistence_options=cache_options
    )
    
    try:
        # Obter novo token
        token_data = credential.get_token(scope)
        
        # Salvar no cache personalizado
        cache.salvar_token(scope, tenant_id, token_data)
        
        print("✅ Autenticação realizada com sucesso! Token salvo no cache.")
        return token_data.token
        
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        raise

# ---------------- API Purview ----------------
def get_purview_entity(guid, token, purview_account):
    url = f"https://{purview_account}.purview.azure.com/catalog/api/atlas/v2/entity/guid/{guid}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# ---------------- Funções para Limpeza de Dados Complexos ----------------
def limpar_dados_para_yaml(dados):
    """
    Prepara os dados para serialização YAML, removendo objetos complexos
    que não podem ser serializados
    """
    if isinstance(dados, dict):
        return {chave: limpar_dados_para_yaml(valor) for chave, valor in dados.items()}
    elif isinstance(dados, list):
        return [limpar_dados_para_yaml(item) for item in dados]
    elif isinstance(dados, (str, int, float, bool)) or dados is None:
        return dados
    else:
        # Converter outros tipos para string
        return str(dados)

def extrair_todas_informacoes(entity_data, purview_account, guid):
    """
    Extrai 100% das informações do endpoint de entity
    """
    dados_completos = {
        # Metadados básicos da entidade principal
        "entity": {
            "guid": entity_data.get("entity", {}).get("guid"),
            "typeName": entity_data.get("entity", {}).get("typeName"),
            "status": entity_data.get("entity", {}).get("status"),
            "createdBy": entity_data.get("entity", {}).get("createdBy"),
            "updatedBy": entity_data.get("entity", {}).get("updatedBy"),
            "createTime": entity_data.get("entity", {}).get("createTime"),
            "updateTime": entity_data.get("entity", {}).get("updateTime"),
            "version": entity_data.get("entity", {}).get("version"),
            "attributes": entity_data.get("entity", {}).get("attributes", {}),
            "classifications": entity_data.get("entity", {}).get("classifications", []),
            "relationshipAttributes": entity_data.get("entity", {}).get("relationshipAttributes", {})
        },
        
        # Todas as entidades referenciadas
        "referredEntities": {
            guid: {
                "typeName": entidade.get("typeName"),
                "guid": entidade.get("guid"),
                "status": entidade.get("status"),
                "attributes": entidade.get("attributes", {}),
                "classifications": entidade.get("classifications", []),
                "relationshipAttributes": entidade.get("relationshipAttributes", {})
            }
            for guid, entidade in entity_data.get("referredEntities", {}).items()
        },
        
        # Metadados adicionais da resposta
        "metadata": {
            "entity_request_url": f"https://{purview_account}.purview.azure.com/catalog/api/atlas/v2/entity/guid/{guid}",
            "timestamp": entity_data.get("timestamp") if 'timestamp' in entity_data else None,
            "purview_account": purview_account
        }
    }
    
    return limpar_dados_para_yaml(dados_completos)

# ---------------- Salvar YAML Completo ----------------
def salvar_yaml_completo(guid, entity_data, purview_account):
    pasta = "Historico"
    os.makedirs(pasta, exist_ok=True)

    # Extrair 100% das informações
    dados_completos = extrair_todas_informacoes(entity_data, purview_account, guid)

    caminho = os.path.join(pasta, f"{guid}_purview_completo.yaml")
    
    # Configurar o dumper YAML para melhor formatação
    class IndentedDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super(IndentedDumper, self).increase_indent(flow, False)
    
    with open(caminho, "w", encoding="utf-8") as f:
        yaml.dump(
            dados_completos, 
            f, 
            allow_unicode=True, 
            sort_keys=False,
            indent=2,
            Dumper=IndentedDumper,
            default_flow_style=False,
            width=1000
        )

    print(f"✅ YAML completo salvo em {caminho}")
    print(f"📊 Tamanho do arquivo: {os.path.getsize(cambia)} bytes")
    
    # Estatísticas do conteúdo
    entity_count = len(dados_completos.get('referredEntities', {}))
    classifications = len(dados_completos.get('entity', {}).get('classifications', []))
    relationship_attrs = len(dados_completos.get('entity', {}).get('relationshipAttributes', {}))
    
    print(f"📈 Estatísticas:")
    print(f"   - Entidades referenciadas: {entity_count}")
    print(f"   - Classificações: {classifications}")
    print(f"   - Atributos de relacionamento: {relationship_attrs}")

# ---------------- Execução Principal ----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python Etapa2.py <GUID>")
        sys.exit(1)

    guid = sys.argv[1]

    try:
        # Carregar configurações do arquivo
        print("📁 Carregando configurações do arquivo Purview...")
        configuracoes = carregar_configuracoes()
        
        purview_account = configuracoes['Purview_account_name']
        print(f"✅ Configurações carregadas. Purview Account: {purview_account}")
        
        # Autenticação com cache
        token = get_access_token(configuracoes)
        
        print(f"📊 Buscando dados completos do GUID: {guid}")
        
        # Buscar dados da entidade (apenas entity, sem lineage)
        entity_data = get_purview_entity(guid, token, purview_account)
        print("✅ Dados da entidade obtidos com sucesso")
        
        # Salvar YAML com 100% das informações (apenas entity)
        salvar_yaml_completo(guid, entity_data, purview_account)
        
    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
        print("💡 Crie o arquivo Credenciais/Purview com as seguintes variáveis:")
        print("Ternant_ID=seu_tenant_id")
        print("Purview_account_name=seu_purview_account")
        print("Scope=https://purview.azure.net/.default")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Erro ao processar GUID {guid}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)