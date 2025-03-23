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

# Configurar o Chrome para rodar no modo headless (sem abrir a interface gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ativa o modo headless

# Inicializar o driver do Chrome com as opções configuradas
driver = webdriver.Chrome(options=chrome_options)

# Configurações do e-mail
EMAIL_REMETENTE = "automacaomrc@gmail.com"  # Seu e-mail
SENHA = "cqle nafe dnmj mwll"  # Senha do e-mail ou app password (recomendado para Gmail)
EMAIL_DESTINATARIO = "mp243822@gmail.com"  # E-mail para receber o CSV

# Função para capturar os dados de uma URL
def capturar_dados(url):
    driver.get(url)
    time.sleep(5)  # Aguarde o carregamento da página

    # Capturar os dados
    dados_produto = {"Link": url}  # Adiciona o link do produto
    
    try:
        # Título do produto
        titulo_elemento = driver.find_element(By.CSS_SELECTOR, "h1.ui-pdp-title")
        dados_produto["Título"] = titulo_elemento.text.strip()
    except:
        dados_produto["Título"] = "N/A"
    
    # Adicionar a data e hora da pesquisa
    dados_produto["Data e Hora"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return dados_produto

# Função para salvar os dados no CSV
def salvar_dados(produtos, arquivo):
    file_exists = os.path.exists(arquivo)

    with open(arquivo, mode="a", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)

        # Se o arquivo não existir, escreve o cabeçalho
        if not file_exists:
            writer.writerow(["Título", "Data e Hora", "Link do Produto"])

        for produto in produtos:
            writer.writerow([produto["Título"], produto["Data e Hora"], produto["Link"]])
        output_file.write("\n\n")

# Ler URLs do arquivo CSV
csv_input_filename = "urls_produtos.csv"  # Nome do arquivo CSV contendo as URLs
csv_output_filename = "dados_produtos.csv"  # Nome do arquivo CSV para salvar os dados

produtos = []

with open(csv_input_filename, mode="r", newline="", encoding="utf-8") as input_file:
    reader = csv.reader(input_file)
    next(reader)  # Pular o cabeçalho, se houver

    for row in reader:
        url = row[0]  # Assumindo que a URL está na primeira coluna
        print(f"🔎Consultando...")
        dados = capturar_dados(url)
        produtos.append(dados)

salvar_dados(produtos, csv_output_filename)
print(f"📂 Dados salvos em {csv_output_filename}")

driver.quit()
enviar_email_com_tabela(produtos_sorted)
