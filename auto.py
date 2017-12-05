# -*- coding: utf-8 -*-

import bs4
import requests
import os

# @link_elems retorna uma lista de links com base no esquema do Lexml
def parsing_module(my_file):
    local_file = open(my_file, 'rb')
    my_file_soup = bs4.BeautifulSoup(local_file, 'lxml')
    link_elems = my_file_soup.findAll('a', {'class' : 'noprint', 'href' : True})
    refs = [] # cria uma lista de referências vazia
    for elem in link_elems:
        refs.append(elem['href'])

# função que realizará os downloads dos documentos dentro das páginas do Lexml
# TODO: descobrir o porquê do get não estar retornando
def download_module(my_url):
    print 'Recebendo de: %s\n' % (my_url)
    my_request = requests.get(my_url, timeout=10)
    print 'Codigo de status: %d' % my_request.status_code
    with open('file1.htm', 'wb') as code:
        code.write(my_request.content)

# função principal
def main():
    path = raw_input('Escolha um diretorio para as operacoes:')
    for filename in os.listdir(path):
        url_local = raw_input("Digite a URL:")
        os.system('clear')
        print 'Baixando arquivo...\n'
        #download_module(url_local)
        main_file = open
