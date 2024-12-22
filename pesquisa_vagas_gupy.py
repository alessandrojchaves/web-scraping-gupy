#importa bibliotecas
import tkinter as tk
import pandas as pd
import time
import os
import sys
from tkinter import simpledialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from pathlib import Path
from datetime import date, timedelta

# Conecta ao Chrome
driver = webdriver.Chrome()
driver.get("https://portal.gupy.io")

root = tk.Tk()
root.withdraw()

# Define a data inicial da consulta
while True:
    data_consulta_str = simpledialog.askstring("Data inicial", "Digite a data do início da pesquisa no formato DD/MM/AAAA:", initialvalue=(date.today() - timedelta(days=1)).strftime("%d/%m/%Y"))

    # Se o usuário cancelar, aborta a execução
    if data_consulta_str is None:
        driver.quit()
        sys.exit("Operação cancelada.")

    # Valida formato da data
    try:
        data_consulta = datetime.strptime(data_consulta_str, "%d/%m/%Y").date()
        break
    except ValueError:
        messagebox.showerror("Erro", "Data inválida! Use o formato DD/MM/AAAA.")

# Lista de termos padrão para excluir dos resultados da consulta
palavras_excluidas = ["Aprendiz",
                      "Assistente",
                      "Estagiária",
                      "Estagiário",
                      "Estágio"]

# Abre a caixa de diálogo para confimar e/ou editar a lista de termos para exclusão

texto_exclusao = simpledialog.askstring("Lista de Exclusão", "Digite os termos para remover da sua pesquisa (itens separados por vírgula):",initialvalue=", ".join(palavras_excluidas))

# Verifica se o usuário cancelou a operação
if texto_exclusao is None:
    messagebox.showinfo("Lista de Exclusão", "Operação cancelada. Nenhum termo será excluído do resultado final.")
    itens_tratados= []

# Processa a lista
else:
    # Separa os itens por vígula e cria uma lista
    itens = texto_exclusao.split(",")
    itens_tratados = [item.strip() for item in itens] # Remove espaços em branco extras

# Limpa os arquivos .csv do diretório de trabalho
for item in os.listdir():
    if os.path.isfile(item) and item.lower().endswith(".csv"):
          try:
              # Excluir o arquivo
              os.remove(item)
              print(f"Arquivo excluído: {item}")
          except OSError as e:
              print(f"Erro ao excluir o arquivo {item}: {e}")
              
# A função abaixo acessa a Gupy, pesquisa o termo e salva os resultados em um arquivo .csv
def pesquisa_vagas(texto_pesquisa, data_pesquisa):
    # Trata o texto a ser pesquisado
    texto_browser  = texto_pesquisa.replace(" ", "%20")
    texto_arquivos = texto_pesquisa.replace(" ", "_").lower()

    # Acessa a página da Gupy com o texto a ser pesquisado
    driver.get("https://portal.gupy.io/job-search/term=" + texto_browser)
    
    # Aguarda o carregamento da página e cancela o processo caso o tempo limite seja atingido
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "sc-4d881605-0")))
    except TimeoutException:
        print("Tempo limite excedido ao aguardar pelos elementos da página.")
        driver.quit()
        exit()

    # Verifica quantidade de vagas encontradas
    try:
        texto_qtde_vagas = driver.find_element(By.CSS_SELECTOR, 'p[data-testid="result-total-text"]').text
    except NoSuchElementException:
        print("Elemento não encontrado.")

    partes_qtde_vagas = texto_qtde_vagas.split(" e ")
    
    if len(partes_qtde_vagas) == 1:
        numero_vagas_texto = partes_qtde_vagas[0].split(" ")[0]
        try:
            numero_vagas = int(numero_vagas_texto)
            print(f"Foram localizadas {numero_vagas} vagas para o termo pesquisado.")
        except ValueError:
            print(f"Não foi possível converter '{numero_vagas_texto}' para um número inteiro.")
            numero_vagas = 300
    elif len(partes_qtde_vagas) > 1:
        numero_vagas_texto = partes_qtde_vagas[1].split(" ")[0]
        try:
            numero_vagas = int(numero_vagas_texto)
            print(f"Foram localizadas {numero_vagas} vagas para o termo pesquisado.")
        except ValueError:
            print(f"Não foi possível converter '{numero_vagas_texto}' para um número inteiro.")
            numero_vagas = 300
    else:
        print("O texto não está no formato esperado.")
        numero_vagas = 300


    # A Gupy mostra 10 vagas de cada vez, sendo necessário rolar até  fim da página para visualizar o restante
    for i in range (1, int(numero_vagas / 10) + 3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        print("Scroll ", i)
        time.sleep(3)


   # Lista para armazenar os dados extraídos
    data = []
    
    # Localiza os elementos das vagas
    vagas = driver.find_elements(By.CLASS_NAME, "sc-4d881605-0")
    
    # Data mínima para filtrar as vagas
    data_minima = datetime.strptime(data_pesquisa, "%d/%m/%Y")
    
    # Extrai as informações de cada vaga
    for vaga in vagas:
        try:
            # Título da Vaga
            titulo = vaga.find_element(By.CLASS_NAME, "sc-4d881605-4").text
    
    
            # Verifica se o título contém alguma palavra excluída
            if any(palavra.lower() in titulo.lower() for palavra in itens_tratados):
                continue  # Pular para a próxima vaga
    
            # Empresa
            empresa = vaga.find_element(By.CLASS_NAME, "sc-4d881605-5").text
    
            # Localização
            try:
                localizacao = vaga.find_element(
                    By.CSS_SELECTOR, '[aria-label^="Local de trabalho:"]'
                ).text
            except NoSuchElementException:
                localizacao = "Não Definido"
    
            # Modelo de Trabalho
            try:
                modelo = vaga.find_element(
                    By.CSS_SELECTOR, '[aria-label^="Modelo de trabalho"]'
                ).text
            except NoSuchElementException:
                modelo = "Não Definido"
                
            # Tipo de Vaga
            try:
                tipo = vaga.find_element(
                    By.CSS_SELECTOR, '[aria-label^="Essa vaga é do tipo"]'
                ).text
            except NoSuchElementException:
                tipo = "Não Definido"
    
            # Data de Publicação
            data_publicacao_texto = vaga.find_element(By.CLASS_NAME, "sc-d9e69618-0").text
            data_publicacao = data_publicacao_texto.replace("Publicada em: ", "")
    
            # Converte a data de publicação para datetime
            try:
                data_publicacao_dt = datetime.strptime(data_publicacao, "%d/%m/%Y")
            except ValueError:
                print(
                    f"Erro ao converter a data de publicação: '{data_publicacao}'. Formato inválido."
                )
                continue  # Pula para a próxima vaga se o formato da data for inválido
    
            # Verifica se a data de publicação é anterior à data mínima
            if data_publicacao_dt < data_minima:
                continue  # Pular para a próxima vaga
    
            # Link da Vaga
            link = vaga.find_element(By.TAG_NAME, "a").get_attribute("href")
            link_final = link.replace("&amp;", "&")  # Corrigir a URL
    
            # Adiciona os dados à lista
            data.append(
                [
                    titulo,
                    empresa,
                    localizacao,
                    modelo,
                    tipo,
                    data_publicacao,
                    link_final,
                ]
            )
    
        except Exception as e:
            print(f"Erro ao extrair dados da vaga: {e}")
    
    
    # Cria um DataFrame do Pandas com os dados
    df = pd.DataFrame(
        data,
        columns=[
            "Título",
            "Empresa",
            "Localização",
            "Modelo de Trabalho",
            "Tipo de Vaga",
            "Data de Publicação",
            "Link",
        ],
    )
    
    # Salva o DataFrame em um arquivo CSV
    df.to_csv("vagas_" + texto_arquivos.lower() + ".csv", index=False, encoding="utf-8-sig")
    
    print("Pesquisa para " + texto_pesquisa + " salva com sucesso em vagas_" + texto_arquivos.lower() + ".csv")


pesquisa_vagas("Dados", data_consulta_str)
pesquisa_vagas("Data", data_consulta_str)
pesquisa_vagas("Analytics", data_consulta_str)


# Nome do arquivo a ser verificado e excluído
nome_arquivo = "arquivo_combinado.csv"

# Verifica se o arquivo existe
if os.path.exists(nome_arquivo):
    # Excluir o arquivo
    os.remove(nome_arquivo)
    print(f"O arquivo '{nome_arquivo}' foi excluído com sucesso.")
else:
    print(f"O arquivo '{nome_arquivo}' não existe.")
    
# Especificar o caminho para a pasta que contém os arquivos CSV.
pasta = Path(os.getcwd())

# Cria uma lista com os DataFrames lidos de cada arquivo CSV na pasta.
lista_dfs = [
    pd.read_csv(arquivo)
    for arquivo in pasta.glob("*.csv")
    if arquivo.is_file()]

# Concatena todos os DataFrames da lista em um único DataFrame.
df_final = pd.concat(lista_dfs, ignore_index=True)

# Salva o DataFrame final em um novo arquivo CSV.
df_final.to_csv("arquivo_combinado.csv", index=False)



# Fechar o navegador
driver.quit()

