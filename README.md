# Pipeline de Cadastro e Coleta (Purview + Dremio + Documentos)

Projeto com 4 etapas + orquestrador (`main.py`) para:
1. Receber input do usuário via Streamlit (GUID, nome da tabela Dremio, links Confluence).
2. Buscar metadados completos no Purview (entity + lineage) e salvar YAML.
3. Fazer amostra (200 linhas aleatórias) da tabela no Dremio e salvar CSV.
4. (Opcional) Baixar páginas indicadas e salvar como PDF (via Playwright).

Todos os artefatos ficam em `Historico/`:
- `{{guid}}.yaml` (dados da Etapa 1)
- `{{guid}}_purview.yaml` (dados do Purview)
- `{{guid}}_amostra.csv` (amostra do Dremio)
- `{{guid}}_doc1.pdf`, `{{guid}}_doc2.pdf`, ... (docs baixados)

---

## Arquivos principais

- `main.py` - Orquestrador com interface Streamlit.
- `Etapa2.py` - Consulta Purview e gera `{guid}_purview.yaml`.
- `Etapa3.py` - Consulta Dremio e gera `{guid}_amostra.csv`.
- `Etapa4_playwright.py` - Gera PDFs dos links (Playwright).
- `requirements.txt` - Lista de dependências (tem instruções de instalação com `--trusted-host`).

---

## Requisitos de sistema / pré-requisitos

- Python 3.9+ (recomendo 3.10+)
- Acesso à rede para PyPI e download do browser do Playwright
- Variáveis de ambiente (defina conforme sua infra):
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_ID`
  - `AZURE_CLIENT_SECRET`
  - `PURVIEW_ACCOUNT_NAME`
  - `DREMIO_HOST`
  - `DREMIO_PORT` (opcional, default 31010)
  - `DREMIO_USER`
  - `DREMIO_PASSWORD`

- Se usar conexão ODBC com Dremio: driver ODBC do Dremio instalado e configurado.

---

## Instalação (ambiente com certificado OK)

```bash
# criar e ativar venv
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# instalar dependências
pip install -r requirements.txt

# instalar browsers do playwright
playwright install
