# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.2

import bs4
import requests
import os, glob

# função de parsing coleta atributos sobre os metadados e chama a função de baixar
# as urls contidas nesses dados
def parsing_module(my_file):
    print("Parsing file %s...\n\n" % (my_file))
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
    for ref in refs:
        download_module(ref, titulo)

# função que realizará os downloads dos documentos dentro das páginas do Lexml
def download_module(my_url, title):
    local_title = title
    #para remover caracteres invalidos na hora de salvar o arquivo
    for ch in ['/', '-', ' ', ';', ':', '.']:
        local_title = local_title.replace(ch, '_')
    print('Recebendo de: %s\n' % my_url)
    my_request = requests.get(my_url)
    print('Codigo de status: %d' % my_request.status_code)
    with open('%s.pdf' % (local_title), 'wb') as f:
        f.write(my_request.content)

# função principal
# TODO: Implementar módulo que utiliza wget. Quando salvar os arquivos, lembrar
#       de salvar com a extensão .html no final.
def main():
    #path = input('Escolha o diretorio que contem os arquivos a serem processados:\n')
    path = '/home/samuel/Next/test2/'
    if os.path.exists(path):
        for filename in glob.glob(os.path.join(path, '*.html')):
            local_file = open(filename, 'rb')
            soup = bs4.BeautifulSoup(local_file, 'lxml')
            print(type(soup))
            local_refs = parsing_module(filename)
            for ref in local_refs:
                print(ref)
            print('\n\n')
            local_file.close()
    else:
        print("Forneca um caminho valido!\n")
