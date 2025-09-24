import streamlit as st
import subprocess
import os
import yaml

HISTORICO_DIR = "Historico"
os.makedirs(HISTORICO_DIR, exist_ok=True)

# ----------------- Funções Auxiliares -----------------

def run_script(script, args=[]):
    """Executa um script python externo e captura o retorno"""
    try:
        result = subprocess.run(
            ["python", script] + args,
            capture_output=True,
            text=True,
            check=True
        )
        st.success(f"✅ {script} executado com sucesso")
        st.text(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Erro ao executar {script}")
        st.text(e.stderr)
        return False

def carregar_yaml(guid):
    caminho = os.path.join(HISTORICO_DIR, f"{guid}.yaml")
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------- APP -----------------

st.title("🚀 Pipeline de Processamento de Tabelas")

# ---- ETAPA 1 ----
st.header("Etapa 1 - Preenchimento de Informações")
with st.form("form_etapa1"):
    guid = st.text_input("GUID da Tabela (Purview)")
    dremio_table = st.text_input("Nome da Tabela no Dremio")
    links = st.text_area("Links de documentação (um por linha)", "").splitlines()
    submitted = st.form_submit_button("Salvar Etapa 1")

if submitted:
    dados = {
        "guid": guid,
        "dremio_table": dremio_table,
        "confluence_docs": [l.strip() for l in links if l.strip()]
    }
    caminho = os.path.join(HISTORICO_DIR, f"{guid}.yaml")
    with open(caminho, "w", encoding="utf-8") as f:
        yaml.dump(dados, f, allow_unicode=True, sort_keys=False)
    st.success(f"✅ Etapa 1 concluída! YAML salvo em {caminho}")

# ---- EXECUTAR PIPELINE ----
if st.button("▶️ Executar Pipeline (Etapas 2, 3 e 4)"):
    if not guid:
        st.error("⚠️ Preencha primeiro a Etapa 1")
    else:
        ok2 = run_script("Etapa2.py", [guid])
        ok3 = run_script("Etapa3.py", [guid])

        # etapa 4 só roda se houver links
        dados = carregar_yaml(guid)
        links = dados.get("confluence_docs", [])
        ok4 = None
        if links:
            ok4 = run_script("Etapa4_playwright.py", [guid])
        else:
            st.info("ℹ️ Nenhum link de documentação informado, pulando Etapa 4.")

        if ok2 and ok3:
            st.success("🎉 Etapas 1, 2 e 3 concluídas com sucesso!")
            if ok4 or ok4 is None:
                st.info("📌 Deseja prosseguir para a etapa de IA?")
                confirmar = st.button("✅ Sim, continuar")
                if confirmar:
                    st.success("🚀 Avançando para a etapa com IA...")
