import os
import yaml
import streamlit as st

# Configuração inicial
st.set_page_config(page_title="Cadastro de Tabelas", page_icon="📊", layout="centered")

st.title("📊 Enriquecimento de Metadados (Purview + Dremio + Confluence)")

# Subtexto adicionado
st.markdown("""
**Preencha o GUID da tabela dentro do Purview, seguido do nome da tabela no Dremio e se houver adicione links do confluence com documentações sobre a tabela ou sobre o produto relacionado para enriquecer a descrição gerada pela IA.**

Dúvidas acesse: Governançapirilampa.com
""")

# Inputs do usuário
guid = st.text_input("GUID da Tabela (Purview)")
tabela = st.text_input("Nome da Tabela (Dremio)")
docs = st.text_area("Links de Documentações (Confluence) (um por linha)")

# Botão para salvar
if st.button("Salvar YAML"):
    if not guid or not tabela:
        st.error("⚠️ GUID e Nome da tabela são obrigatórios.")
    else:
        # Montar dados
        dados = {
            "guid": guid,
            "dremio_table": tabela,
            "confluence_docs": [doc.strip() for doc in docs.splitlines() if doc.strip()]
        }

        # Criar pasta Historico
        pasta = "Historico"
        os.makedirs(pasta, exist_ok=True)

        # Nome do arquivo com GUID
        caminho_arquivo = os.path.join(pasta, f"{guid}.yaml")

        # Salvar YAML
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            yaml.dump(dados, f, allow_unicode=True, sort_keys=False)

        st.success(f"✅ Arquivo salvo em `{caminho_arquivo}`")
        st.code(yaml.dump(dados, allow_unicode=True, sort_keys=False), language="yaml")