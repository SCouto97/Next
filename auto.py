# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.2

import bs4, requests, os, sys, glob, errno, mimetypes, re

def download(url, num_retries=2):
    print('Downloading: %s' % url)
    request = requests.get(url)
    html = request.text
# função de parsing coleta atributos sobre os metadados e chama a função de baixar
# as urls contidas nesses dados
def parsing_module(my_file, downl_dir):
    print("Parsing file %s...\n" % (my_file))
    local_file = open(my_file, 'rb')
    soup = bs4.BeautifulSoup(local_file, 'lxml')
    desc_elems = soup.findAll('div', {'class' : 'result_col2'})
    localidade = desc_elems[0].text
    autoridade = desc_elems[1].text
    titulo = desc_elems[2].text
    data = desc_elems[3].text
    # ext_tag = '<div class="result_col23">'
    # ext_soup = bs4.BeautifulSoup(ext_tag, 'lxml').text
    # ext_chunk = ext_soup.find('span', {'class' : 'noprint'})
    # file_type = ext_chunk.split('/')
    # extension = file_type[1]
    # if extension.endswith(' ) '):
    #     extension = extension[:-3]
    # print('\n\n\ndebug value: %s\n\n\n' % extension)
    url_elems = soup.findAll('a', {'class' : 'noprint', 'href' : True})
    refs = [] # cria uma lista de referências vazia
    for elem in url_elems:
        refs.append(elem['href'])
    valid_urls = [x for x in refs if "lex" not in x]
    valid_urls = [x for x in valid_urls if "legislacao" not in x]
    for url in valid_urls:
        download_module(my_url=url, title=titulo, downl_path=downl_dir, ext='pdf')

# função que realizará os downloads dos documentos dentro das páginas do Lexml
# problema no site http://legislacao.planalto.gov.br
# TODO: tratar exceção 404
def download_module(my_url, title, downl_path, ext):
    local_title = title
    #para remover caracteres invalidos na hora de salvar o arquivo
    for ch in ['/', '-', ' ', ';', ':', '.', 'º', 'ª', ',']:
        local_title = local_title.replace(ch, '')
    print('Receiving from: %s' % my_url)
    try:
        my_request = requests.get(my_url, timeout=10)
        print('HTTP status code: %d' % my_request.status_code)
        print('Request OK\n')
    except requests.exceptions.RequestException as e:
        print('ERROR')
        return

    with open('%s/%s.%s' % (downl_path, local_title, ext), 'wb') as f:
        f.write(my_request.content)

def crawl_sitemap():
    url = input('escreva o sitemap que deseja baixar:\n');
    sitemap = requests.get(url).text
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    count = 0
    for link in links:
        print('link: %s\n' % link)
        count += 1
    print('No de paginas acessadas: %d\n' % count)

# função principal
# TODO: Implementar função para adquirir os dados do sitemap lexml
def main():

    file_path = './test2/'
    directory = input("Select a directory to store the downloaded files:\n")
    directory = "./%s" % (directory)
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    if os.path.exists(file_path):
        for filename in glob.glob(os.path.join(file_path, '*.html')):
            local_file = open(filename, 'rb')
            soup = bs4.BeautifulSoup(local_file, 'lxml')
            parsing_module(filename, directory)
            local_file.close()
    else:
        print("Forneca um caminho valido!\n")

main()
