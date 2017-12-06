# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.1

import bs4
import requests
import os

# @link_elems retorna uma lista de links com base no esquema do Lexml
# por enquanto retorna apenas a lista de referencias
# TODO: -parsing coletar outros atributos sobre dado arquivo
#       -resolver o problema do encoding, de alguma forma(problema parece ser da parte do servidor)
def parsing_module(my_file):
    local_file = open(my_file, 'rb')
    soup = bs4.BeautifulSoup(local_file, 'lxml')
    desc_elems = soup.findAll('div', {'class' : 'result_col2'})
    localidade = desc_elems[0].text
    autoridade = desc_elems[1].text
    titulo = desc_elems[2].text
    data = desc_elems[3].text
    url_elems = soup.findAll('a', {'class' : 'noprint', 'href' : True})
    refs = [] # cria uma lista de referências vazia
    for elem in url_elems:
        refs.append(elem['href'])
    close(local_file)
    return refs

# função que realizará os downloads dos documentos dentro das páginas do Lexml
# TODO: descobrir o porquê do get não estar retornando
def download_module(my_url):
    print 'Recebendo de: %s\n' % (my_url)
    my_request = requests.get(my_url, timeout=10)
    print 'Codigo de status: %d' % my_request.status_code
    with open('file1.htm', 'wb') as code:
        code.write(my_request.content)

# função principal
# TODO: Escolher uma lógica mais bem elaborada para a função principal:
#       - Baixar tudo -> parsing no diretório (ou)
#       - Baixa um por vez -> parsing individual (?)
def main():
    path = input('Escolha um diretorio para as operacoes:')
    for filename in os.listdir(path):

        #local_ref = []
        #local_ref = parsing_module(filename)
