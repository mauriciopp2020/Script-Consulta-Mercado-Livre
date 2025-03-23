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

    try:
        # Preço com desconto
        preco_meta_elemento = driver.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]')
        dados_produto["Preço"] = float(preco_meta_elemento.get_attribute("content").replace(',', '.'))
    except:
        dados_produto["Preço"] = float('inf')  # Se não tiver preço, define um valor alto
    
    # Adicionar a data e hora da pesquisa
    dados_produto["Data e Hora"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return dados_produto

# Função para ler os preços antigos de um arquivo CSV
def ler_precos_anteriores(arquivo):
    precos_anteriores = {}
    if os.path.exists(arquivo):
        with open(arquivo, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Armazenar os preços antigos usando o título como chave
                precos_anteriores[row["Título"]] = float(row["Preço"])
    return precos_anteriores

# Função para salvar os dados no CSV
def salvar_dados(produtos, arquivo):
    file_exists = os.path.exists(arquivo)

    with open(arquivo, mode="a", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)

        # Se o arquivo não existir, escreve o cabeçalho
        if not file_exists:
            writer.writerow(["Título", "Preço", "Alteração de Preço", "Data e Hora", "Link do Produto"])

        # Adicionar duas linhas vazias após cada consulta de produto (não entre as colunas)
        for produto in produtos:
            # Escrever os dados no CSV
            writer.writerow([produto["Título"], produto["Preço"], produto["Alteração de Preço"], produto["Data e Hora"], produto["Link"]])
        output_file.write("\n\n")

# Função para enviar o e-mail com o CSV anexado e em formato de tabela HTML no corpo com responsividade e negrito
def enviar_email_com_tabela(produtos):
    msg = EmailMessage()
    msg["Subject"] = "Relatório de Preços - E-commerce Mercado Livre"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg.set_content("Segue abaixo o relatório de preços atualizado.")

    # Criando a tabela HTML com CSS responsivo e negrito nas linhas
    html_content = """
    <html>
    <head>
        <style>
            /* Estilo para a tabela */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 8px;
                text-align: left;
                border: 1px solid #ddd;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            td {
                font-weight: bold; /* Adiciona negrito nas células */
            }
            /* Estilo para o link */
            a {
                text-decoration: none;
                color: #0066cc;
            }
            /* Responsividade */
            @media screen and (max-width: 600px) {
                table {
                    width: 100%;
                    display: block;
                    overflow-x: auto;
                }
                th, td {
                    display: block;
                    width: 100%;
                }
                td {
                    text-align: right;
                    padding-left: 50%;
                    position: relative;
                }
                td::before {
                    content: attr(data-label);
                    position: absolute;
                    left: 10px;
                    font-weight: bold;
                }
            }
        </style>
    </head>
    <body>
        <h3>📊 Tabela de Preço dos produtos do E-commerce Mercado Livre 📊</h3>
        <table>
            <tr>
                <th>Título</th>
                <th>Preço</th>
                <th>Alteração de Preço</th>
                <th>Data e Hora</th>
                <th>Link do Produto</th>
            </tr>
    """
    
    for produto in produtos:
        html_content += f"""
            <tr>
                <td>{produto["Título"]}</td>
                <td>{produto["Preço"]}</td>
                <td>{produto["Alteração de Preço"]}</td>
                <td>{produto["Data e Hora"]}</td>
                <td><a href="{produto["Link"]}">Link</a></td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    msg.add_alternative(html_content, subtype="html")


    # Enviar o e-mail via SMTP
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_REMETENTE, SENHA)
        server.send_message(msg)

    print("📧 E-mail enviado com sucesso!")

# Ler URLs do arquivo CSV
csv_input_filename = "urls_produtos.csv"  # Nome do arquivo CSV contendo as URLs
csv_output_filename = "dados_produtos.csv"  # Nome do arquivo CSV para salvar os dados

# Ler os preços antigos
precos_anteriores = ler_precos_anteriores(csv_output_filename)

produtos = []

with open(csv_input_filename, mode="r", newline="", encoding="utf-8") as input_file:
    reader = csv.reader(input_file)
    next(reader)  # Pular o cabeçalho, se houver

    # Iterar sobre as URLs e coletar os dados
    for row in reader:
        url = row[0]  # Assumindo que a URL está na primeira coluna
        print(f"🔎Consultando...")
        dados = capturar_dados(url)
        
        # Verificar se houve aumento ou diminuição no preço
        alteracao_preco = "Sem Alteração"
        cor = "black"
        if dados["Título"] in precos_anteriores:
            diferenca = dados["Preço"] - precos_anteriores[dados["Título"]]
            if diferenca > 0:
                alteracao_preco = f"Aumento de R${diferenca:.2f}"
                cor = "red"
            elif diferenca < 0:
                alteracao_preco = f"Diminuição de R${-diferenca:.2f}"
                cor = "green"
        
       
        # Para o e-mail, inclui a formatação HTML para a cor
        produto_html = {
            "Título": dados["Título"],
            "Preço": dados["Preço"],
            "Alteração de Preço": f'<span style="color:{cor}; font-weight:bold;">{alteracao_preco}</span>',
            "Data e Hora": dados["Data e Hora"],
            "Link": dados["Link"]
        }
        dados["Alteração de Preço"] = alteracao_preco
        produtos.append(produto_html)

# Ordenar os produtos por preço (do menor para o maior)
produtos_sorted = sorted(produtos, key=lambda x: x["Preço"])

salvar_dados(produtos_sorted, csv_output_filename)
print(f"📂 Dados salvos em {csv_output_filename}")

driver.quit()

# Perguntar ao usuário se deseja enviar o e-mail
enviar_email = input("📧 Deseja enviar o relatório por e-mail? (s/n): ").strip().lower()
if enviar_email == 's':
   enviar_email_com_tabela(produtos_sorted)
