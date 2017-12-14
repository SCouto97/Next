# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.4

import bs4, requests, os, sys, glob, errno, mimetypes, re

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
    ext_elems = soup.findAll('span', {'class' : 'noprint'})
    l = []
    for e in ext_elems:
        r = re.findall('doc', e.text)
        if(len(r) != 0):
            l.append(r)
    if(len(l) != 0):
        extension = 'doc'
    else:
        extension = 'pdf'
    url_elems = soup.findAll('a', {'class' : 'noprint', 'href' : True})
    refs = [] # cria uma lista de referências vazia
    for elem in url_elems:
        refs.append(elem['href'])
    valid_urls = [x for x in refs if "lex" not in x]
    valid_urls = [x for x in valid_urls if "legislacao" not in x]
    for url in valid_urls:
        download_module(my_url=url, title=titulo, downl_path=downl_dir, ext=extension)

# função que realizará os downloads dos documentos dentro das páginas do Lexml
# foi generalizada para baixar links do sitemap
# problema no site http://legislacao.planalto.gov.br
# TODO: tratar exceção 404
def download_module(my_url, title, downl_path, ext):
    local_title = title
    #para remover caracteres invalidos na hora de salvar o arquivo
    directory = "./%s" % (downl_path)
    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
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

    with open('%s/%s.%s' % (directory, local_title, ext), 'wb') as f:
        f.write(my_request.content)

# função que obtém os arquivos de metadados dos sites do lexml
def crawl_sitemap():
    url = input('escreva o sitemap que deseja baixar:\n');
    sitemap = requests.get(url).text
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    count = 0
    for link in links:
        count += 1
        sep = link.split('/')
        nome = sep[4]
        extension = 'html'
        download_module(my_url=link, downl_path='sitemap_data', title=nome, ext=extension)
    print('Number of pages crawled: %d\n' % count)

# função criada para tentar corrigir alguns erros de extensão
# feita para ser usada em loop dentro de um diretório
def extension_converter_aux(filename, new_extension):
    l = filename.split('.')
    ext = l[len(l)-1]
    l[len(l)-1] = new_extension
    filename = '.'.join(l)
    return filename
# função para mudar extensões dentro de um diretório(usar quando tiver erros de extensão)
def extension_converter(path):
    old = '*.pdf'
    new = 'html'
    for filename in glob.glob(os.path.join(path, old)):
        filename_new = extension_converter_aux(filename, new)
        print('Old file name: %s' % filename_new)
        os.rename(filename, filename_new)
        print('Renamed to: %s' % new)

# função principal
# TODO: Implementar função para adquirir os dados do sitemap lexml
def main():

    file_path = './t3/'
    directory = input("Select a directory to store the downloaded files:\n")
    if os.path.exists(file_path):
        for filename in glob.glob(os.path.join(file_path, '*.html')):
            local_file = open(filename, 'rb')
            soup = bs4.BeautifulSoup(local_file, 'lxml')
            parsing_module(filename, directory)
            local_file.close()
    else:
        print("Forneca um caminho valido!\n")
