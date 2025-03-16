import time
import csv
import smtplib
import ssl
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import os
import pytz 

# Configurar fuso horário do Brasil
fuso_horario_brasil = pytz.timezone('America/Sao_Paulo')

# Configurar ChromeOptions para rodar no GitHub Actions
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/google-chrome"
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializar WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Configurações do e-mail
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")  # Pegando do GitHub Secrets
SENHA = os.getenv("EMAIL_SENHA")  # Pegando do GitHub Secrets
EMAIL_DESTINATARIO = "mp243822@gmail.com"

# Função para capturar os dados de uma URL
def capturar_dados(url):
    driver.get(url)
    time.sleep(5)

    dados_produto = {"Link": url}  
    
    try:
        titulo_elemento = driver.find_element(By.CSS_SELECTOR, "h1.ui-pdp-title")
        dados_produto["Título"] = titulo_elemento.text.strip()
    except:
        dados_produto["Título"] = "N/A"

    try:
        preco_meta_elemento = driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]')
        dados_produto["Preço"] = float(preco_meta_elemento.get_attribute("content").replace(',', '.'))
    except:
        dados_produto["Preço"] = float('inf')

    data_hora_local = datetime.now(fuso_horario_brasil).strftime("%d/%m/%Y %H:%M:%S")
    dados_produto["Data e Hora"] = data_hora_local
    
    return dados_produto

# Função para salvar os dados no CSV
def salvar_dados(produtos, arquivo):
    file_exists = os.path.exists(arquivo)

    print(f"🔹 Tentando salvar {len(produtos)} produtos em {arquivo}...")

    with open(arquivo, mode="w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)

        if not file_exists:
            writer.writerow(["Título", "Preço", "Alteração de Preço", "Data e Hora", "Link do Produto"])

        for produto in produtos:
            writer.writerow([produto["Título"], produto["Preço"], produto["Alteração de Preço"], produto["Data e Hora"], produto["Link"]])

    print("✅ Dados salvos com sucesso!")

# Função para enviar o e-mail com o CSV
def enviar_email_com_tabela(arquivo_csv):
    print("📧 Enviando e-mail com relatório...")
    
    msg = EmailMessage()
    msg["Subject"] = "📊 Relatório de Preços - Mercado Livre"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg.set_content("Segue o relatório atualizado dos preços.")

    with open(arquivo_csv, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="csv", filename="relatorio_precos.csv")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_REMETENTE, SENHA)
            server.send_message(msg)
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")

# Arquivos CSV
csv_output_filename = "/tmp/dados_produtos.csv"

produtos = []

# Ler URLs do arquivo CSV
csv_input_filename = "urls_produtos.csv"

if os.path.exists(csv_input_filename):
    with open(csv_input_filename, mode="r", newline="", encoding="utf-8") as input_file:
        reader = csv.reader(input_file)
        next(reader)

        for row in reader:
            url = row[0]  
            print(f"🔎 Consultando {url}...")
            dados = capturar_dados(url)

            dados["Alteração de Preço"] = "Sem Alteração"
            produtos.append(dados)

    salvar_dados(produtos, csv_output_filename)
    print(f"📂 Dados salvos em {csv_output_filename}")

    # Enviar e-mail com CSV
    enviar_email_com_tabela(csv_output_filename)

else:
    print(f"❌ O arquivo {csv_input_filename} não foi encontrado!")

# Fechar navegador
driver.quit()
