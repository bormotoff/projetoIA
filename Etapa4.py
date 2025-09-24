import os
import sys
import yaml
import asyncio
from playwright.async_api import async_playwright

# ---------------- Carregar YAML ----------------
def carregar_yaml(guid):
    caminho = os.path.join("Historico", f"{guid}.yaml")
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"❌ Arquivo {caminho} não encontrado. Rode a Etapa 1 antes.")
    
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ---------------- Função assíncrona para baixar PDFs ----------------
async def baixar_pdfs(guid, links):
    pasta = "Historico"
    os.makedirs(pasta, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        for i, link in enumerate(links, start=1):
            caminho_pdf = os.path.join(pasta, f"{guid}_doc{i}.pdf")
            try:
                page = await context.new_page()
                await page.goto(link, timeout=60000)  # 60s timeout
                await page.pdf(path=caminho_pdf, format="A4")
                print(f"✅ PDF salvo em {caminho_pdf}")
                await page.close()
            except Exception as e:
                print(f"❌ Erro ao baixar {link}: {e}")

        await browser.close()

# ---------------- Execução Principal ----------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python Etapa4_playwright.py <GUID>")
        sys.exit(1)

    guid = sys.argv[1]

    try:
        dados = carregar_yaml(guid)
        links = dados.get("confluence_docs", [])

        if not links:
            print(f"⚠️ Nenhum link de documentação encontrado no YAML de {guid}.")
        else:
            asyncio.run(baixar_pdfs(guid, links))

    except Exception as e:
        print(f"❌ Erro na Etapa 4: {e}")
        sys.exit(1)
