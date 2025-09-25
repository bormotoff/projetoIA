import os
import sys
import yaml
import pandas as pd
import PyPDF2
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def carregar_yaml(path_yaml):
    with open(path_yaml, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def carregar_csv(path_csv, n_linhas=5):
    df = pd.read_csv(path_csv)
    return df, df.head(n_linhas).to_string(index=False)

def carregar_pdf(path_pdf):
    texto = []
    with open(path_pdf, "rb") as f:
        leitor = PyPDF2.PdfReader(f)
        for pagina in leitor.pages:
            texto.append(pagina.extract_text())
    return "\n".join(texto)

def montar_prompt(metadados, amostra, doc):
    return f"""
Analise esta tabela para catálogo de dados corporativo:

**METADADOS:**
{metadados}

**AMOSTRA:**
{amostra}

**DOCUMENTAÇÃO:**
{doc}

**INSTRUÇÕES:**
- Comece com "Preenchido com IA"
- 2 seções: Descrição da tabela e Contexto Negócio
- Foco em produto/negócio - NÃO descreva colunas
- Linguagem técnica para governança
- Seja abrangente e descreva os produtos/serviços ou instrumentos financeiros identificados na tabela
"""

def descrever_colunas(df, metadados):
    """
    Gera descrição detalhada de cada coluna com base na amostra do CSV.
    Se o YAML tiver metadados de colunas, pode ser ajustado aqui.
    """
    descricoes = []
    for coluna in df.columns:
        descricoes.append(f"- {coluna}: Campo da tabela utilizado para armazenar informações relacionadas a '{coluna}'.")
    return "\n".join(descricoes)

def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py <GUID>")
        sys.exit(1)

    guid = sys.argv[1]
    path_yaml = f"{guid}.yaml"
    path_csv = f"{guid}.csv"
    path_pdf = f"{guid}.pdf"

    if not (os.path.exists(path_yaml) and os.path.exists(path_csv) and os.path.exists(path_pdf)):
        print("Erro: Arquivos correspondentes ao GUID não encontrados.")
        sys.exit(1)

    metadados = carregar_yaml(path_yaml)
    df, amostra = carregar_csv(path_csv)
    doc = carregar_pdf(path_pdf)

    prompt = montar_prompt(metadados, amostra, doc)

    resposta = client.chat.completions.create(
        model="gpt-4.0",
        messages=[
            {"role": "system", "content": "Você é um assistente especializado em governança de dados corporativos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    conteudo_ia = resposta.choices[0].message.content.strip()

    descricao_colunas = descrever_colunas(df, metadados)

    path_saida = f"{guid}_IA.txt"
    with open(path_saida, "w", encoding="utf-8") as f:
        f.write(conteudo_ia)
        f.write("\n\n=== DESCRIÇÃO DAS COLUNAS ===\n")
        f.write(descricao_colunas)

    print(f"\n✅ Análise concluída! Resultado salvo em: {path_saida}")

if __name__ == "__main__":
    main()
