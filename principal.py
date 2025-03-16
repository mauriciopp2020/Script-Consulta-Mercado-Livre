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

# Configurar ChromeOptions
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/google-chrome"  # Caminho correto do Chrome
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializar WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Configurações do e-mail
EMAIL_REMETENTE = "automacaomrc@gmail.com"  
SENHA = "cqle nafe dnmj mwll"  
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

# Função para ler os preços antigos do CSV
def ler_precos_anteriores(arquivo):
    precos_anteriores = {}
    if os.path.exists(arquivo):
        with open(arquivo, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                precos_anteriores[row["Título"]] = float(row["Preço"])
    return precos_anteriores

# Função para salvar os dados no CSV
def salvar_dados(produtos, arquivo):
    file_exists = os.path.exists(arquivo)

    with open(arquivo, mode="w", newline="", encoding="utf-8") as output_file:  # Modo "w" sobrescreve o arquivo corretamente
        writer = csv.writer(output_file)

        if not file_exists:
            writer.writerow(["Título", "Preço", "Alteração de Preço", "Data e Hora", "Link do Produto"])

        for produto in produtos:
            writer.writerow([produto["Título"], produto["Preço"], produto["Alteração de Preço"], produto["Data e Hora"], produto["Link"]])

# Função para enviar o e-mail com os dados
def enviar_email_com_tabela(produtos, arquivo_csv):
    msg = EmailMessage()
    msg["Subject"] = "Relatório de Preços - Mercado Livre"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg.set_content("Segue o relatório atualizado.")

    html_content = """
    <html>
    <head>
        <style>
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 8px; text-align: left; border: 1px solid #ddd; }
            th { background-color: #f2f2f2; font-weight: bold; }
            td { font-weight: bold; }
            a { text-decoration: none; color: #0066cc; }
        </style>
    </head>
    <body>
        <h3>Relatório de Preços</h3>
        <table>
            <tr>
                <th>Título</th>
                <th>Preço</th>
                <th>Alteração</th>
                <th>Data</th>
                <th>Link</th>
            </tr>
    """

    for produto in produtos:
        html_content += f"""
            <tr>
                <td>{produto["Título"]}</td>
                <td>{produto["Preço"]}</td>
                <td>{produto["Alteração de Preço"]}</td>
                <td>{produto["Data e Hora"]}</td>
                <td><a href="{produto["Link"]}">Ver</a></td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    msg.add_alternative(html_content, subtype="html")

    with open(arquivo_csv, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="csv", filename=arquivo_csv)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_REMETENTE, SENHA)
        server.send_message(msg)

    print("E-mail enviado com sucesso!")

# Arquivos CSV
csv_input_filename = "urls_produtos.csv"
csv_output_filename = "dados_produtos.csv"

# Ler os preços antigos
precos_anteriores = ler_precos_anteriores(csv_output_filename)

produtos = []

# Ler URLs do arquivo CSV
with open(csv_input_filename, mode="r", newline="", encoding="utf-8") as input_file:
    reader = csv.reader(input_file)
    next(reader)

    for row in reader:
        url = row[0]  
        print(f"Consultando...")
        dados = capturar_dados(url)
        
        alteracao_preco = "Sem Alteração"
        if dados["Título"] in precos_anteriores:
            diferenca = dados["Preço"] - precos_anteriores[dados["Título"]]
            if diferenca > 0:
                alteracao_preco = f"Aumento de R${diferenca:.2f}"
            elif diferenca < 0:
                alteracao_preco = f"Diminuição de R${-diferenca:.2f}"

        dados["Alteração de Preço"] = alteracao_preco
        produtos.append(dados)

# Ordenar produtos e salvar
produtos_sorted = sorted(produtos, key=lambda x: x["Preço"])
salvar_dados(produtos_sorted, csv_output_filename)
print(f"Dados salvos em {csv_output_filename}")

driver.quit()

# Enviar e-mail
enviar_email_com_tabela(produtos_sorted, csv_output_filename)
