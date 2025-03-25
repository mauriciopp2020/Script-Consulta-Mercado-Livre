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

driver = webdriver.Chrome(options=chrome_options)

# Configurações do e-mail
EMAIL_REMETENTE = "automacaomrc@gmail.com"
SENHA = "cqle nafe dnmj mwll"
EMAIL_DESTINATARIO = "mp243822@gmail.com"

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
    
    return dados_produto

def ler_precos_anteriores(arquivo):
    precos_anteriores = {}
    if os.path.exists(arquivo):
        with open(arquivo, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                precos_anteriores[row["Título"]] = float(row["Preço"])
    return precos_anteriores

def salvar_dados(produtos, arquivo):
    file_exists = os.path.exists(arquivo)
    with open(arquivo, mode="a", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        if not file_exists:
            writer.writerow(["Título", "Preço", "Link do Produto"])
        for produto in produtos:
            writer.writerow([produto["Título"], produto["Preço"], produto["Link"]])
        output_file.write("\n\n")

def enviar_email_com_tabela(produtos):
    msg = EmailMessage()
    msg["Subject"] = "Relatório de Preços - E-commerce Mercado Livre"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg.set_content("Segue abaixo o relatório de preços atualizado.")

    html_content = """
    <html>
    <head>
        <style>
            .table-container {
                width: 100%;
                overflow-x: auto;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            a {
                text-decoration: none;
                color: #0066cc;
            }
            @media screen and (max-width: 600px) {
                .table-container {
                    overflow-x: auto;
                }
                table {
                    width: 100%;
                    min-width: 400px;
                }
                th, td {
                    font-size: 14px;
                    white-space: nowrap;
                }
            }
        </style>
    </head>
    <body>
        <h3>📊 Tabela de Preço dos produtos do E-commerce Mercado Livre 📊</h3>
        <div class="table-container">
            <table>
                <tr>
                    <th>Título</th>
                    <th>Preço</th>
                    <th>Link do Produto</th>
                </tr>
    """
    
    for produto in produtos:
        html_content += f"""
                <tr>
                    <td>{produto["Título"]}</td>
                    <td>{produto["Preço"]}</td>
                    <td><a href="{produto["Link"]}">Link</a></td>
                </tr>
        """
    
    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    
    msg.add_alternative(html_content, subtype="html")
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_REMETENTE, SENHA)
        server.send_message(msg)
    print("📧 E-mail enviado com sucesso!")

csv_input_filename = "urls_produtos.csv"
csv_output_filename = "dados_produtos.csv"

precos_anteriores = ler_precos_anteriores(csv_output_filename)

produtos = []
with open(csv_input_filename, mode="r", newline="", encoding="utf-8") as input_file:
    reader = csv.reader(input_file)
    next(reader)
    for row in reader:
        url = row[0]
        print(f"🔎Consultando...")
        dados = capturar_dados(url)
        produto_html = {"Título": dados["Título"], "Preço": dados["Preço"], "Link": dados["Link"]}
        produtos.append(produto_html)

produtos_sorted = sorted(produtos, key=lambda x: x["Preço"])

salvar_dados(produtos_sorted, csv_output_filename)
print(f"📂 Dados salvos em {csv_output_filename}")

driver.quit()

enviar_email_com_tabela(produtos_sorted)
