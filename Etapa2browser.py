import os
import sys
import yaml
import requests
from azure.identity import InteractiveBrowserCredential

# Variáveis de ambiente (apenas Purview account name necessário)
PURVIEW_ACCOUNT = os.getenv("PURVIEW_ACCOUNT_NAME")

# ---------------- Autenticação Purview com Interactive Browser ----------------
def get_access_token():
    """
    Usa InteractiveBrowserCredential para autenticação interativa
    Abre o navegador para login Azure AD
    """
    credential = InteractiveBrowserCredential()
    token = credential.get_token("https://purview.azure.net/.default")
    return token.token

# ---------------- API Purview ----------------
def get_purview_entity(guid, token):
    url = f"https://{PURVIEW_ACCOUNT}.purview.azure.com/catalog/api/atlas/v2/entity/guid/{guid}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_purview_lineage(guid, token):
    url = f"https://{PURVIEW_ACCOUNT}.purview.azure.com/catalog/api/atlas/v2/lineage/{guid}?depth=3"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

# ---------------- Salvar YAML ----------------
def salvar_yaml_purview(guid, entity, lineage):
    pasta = "Historico"
    os.makedirs(pasta, exist_ok=True)

    # Extrair apenas as colunas
    columns = {
        k: v["attributes"]
        for k, v in entity.get("referredEntities", {}).items()
        if v.get("typeName") == "column"
    }

    dados = {
        "guid": guid,
        "qualifiedName": entity.get("entity", {}).get("attributes", {}).get("qualifiedName"),
        "name": entity.get("entity", {}).get("attributes", {}).get("name"),
        "description": entity.get("entity", {}).get("attributes", {}).get("description"),
        "columns": columns,
        "lineage": lineage
    }

    caminho = os.path.join(pasta, f"{guid}_purview.yaml")
    with open(caminho, "w", encoding="utf-8") as f:
        yaml.dump(dados, f, allow_unicode=True, sort_keys=False)

    print(f"✅ YAML salvo em {caminho}")

# ---------------- Execução Principal ----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python Etapa2.py <GUID>")
        sys.exit(1)

    guid = sys.argv[1]

    try:
        print("🔐 Iniciando autenticação interativa...")
        print("📱 Será aberto o navegador para login Azure AD")
        
        token = get_access_token()
        print("✅ Autenticação realizada com sucesso!")
        
        print(f"📊 Buscando dados do GUID: {guid}")
        entity = get_purview_entity(guid, token)
        lineage = get_purview_lineage(guid, token)
        
        salvar_yaml_purview(guid, entity, lineage)
        
    except Exception as e:
        print(f"❌ Erro ao processar GUID {guid}: {e}")
        sys.exit(1)