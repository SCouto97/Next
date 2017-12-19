# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.5

import bs4, requests, os, sys, glob, errno, mimetypes, re

# Convenções nesse programa para comunicação com a api REST:
# Por enquanto só criação para fazer os testes
# Key#:                  Operação:
#    1                    Criar uma comunidade
#    2                    Criar uma sub-comunidade
#    3                    Criar uma coleção
#    4                    Criar um objeto(lei, jurisprudência)

# Protótipo de um artigo do Dspace, utilizado posteriormente para requisições
# com a api REST
class DspaceObject(object):
    def __init__(self, local, authority, name, date, obj_id, parent_id, parent_name):
        self.local = local
        self.authority = authority
        self.name = name
        self.obj_id = obj_id
        self.parent_id = parent_id
        self.parent_name = parent_name

    def create_dictionary(self):
        __dspace_dict = {'local' : self.local, 'authority' : self.authority,
                        'title' : self.name, 'date' : self.date}
        return __dspace_dict

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

# função que faz o teste de submissão no repositório a partir da api REST
def rest_test(op, dspace_obj, com_name, subcom_name, col_name):
    null = None
    ses = requests.session()
    email = 'samuel.a.couto@gmail.com'
    password = 'Senha123'
    login = {'email' : email, 'password' : password}
    link = 'http://dev.jusbot.com.br/rest'
    r = ses.post(url='%s/login' % link, data=login)
    sessionID = ses.cookies['JSESSIONID']
    ses_dic = {'cookie' : sessionID}
    debug = '\n\n sessionId = %s' % sessionID + '\n\n'
    print(debug)
    con_type = {'content-type' : 'application/json'}
    if(r.status_code == 200):
        if(op == 1):
            com_obj = {
                       "id":dspace_obj.obj_id,
                       "name":dspace_obj.name,
                       "handle":"10766/10213",
                       "type":"community",
                       "link":"/rest/communities/"+dspace_obj.obj_id,
                       "expand":["parentCommunity","collections","subCommunities",
                                 "logo","all"],
                       "logo":null,
                       "parentCommunity":null,
                       "copyrightText":"",
                       "introductoryText":"",
                       "shortDescription":"",
                       "sidebarText":"",
                       "countItems":3,
                       "subcommunities":[],
                       "collections":[]
                      }
            ccom = ses.post(url='%s/communities'%server, headers=con_type,
                            json=com_obj, cookies=ses_dic)
        elif(op == 2):
            subcom_obj = {
                          "id":dspace_obj.obj_id,
                          "name":dspace_obj.name,
                          "handle":"10766/10213",
                          "type":"community",
                          "link":"/rest/communities/"+dspace_obj.obj_id,
                          "expand":["parentCommunity","collections","subCommunities",
                                    "logo","all"],
                          "logo":null,
                          "parentCommunity":dspace_obj.parent_name,
                          "copyrightText":"",
                          "introductoryText":"",
                          "shortDescription":"",
                          "sidebarText":"",
                          "countItems":3,"subcommunities":[],
                          "collections":[]
                         }
            sccom = ses.post(url='%s/communities/%d/communities'%(server, dspace_obj.parent_id),
                                  headers=con_type, json=subcom_obj, cookies=ses_dic)
        elif(op == 3):
            col_obj = {
                       "id":dspace_obj.obj_id,
                       "name":dspace_obj.name,
                       "handle":"10766/10214",
                       "type":"collection",
                       "link":"/rest/collections/"+dspace_obj.obj_id,
                       "expand":["parentCommunityList","parentCommunity","items","license",
                                 "logo","all"],
                       "logo":null,
                       "parentCommunity":null,
                       "parentCommunityList":[],
                       "items":[],"license":null,
                       "copyrightText":"",
                       "introductoryText":"",
                       "shortDescription":"",
                       "sidebarText":"",
                       "numberItems":3
                      }
            ccol = ses.post(url='%s/communities/%d/collections'%(server, dspace_obj.parent_id),
                                 headers=con_type, json=col_obj, cookies=ses_dic)
        elif(op == 4):
            new_obj = {
                       "id":dspace_obj.obj_id,
                       "name":"2015 Annual Report",
                       "handle":"123456789/13470",
                       "type":"item",
                       "link":"/rest/items/"+dspace_obj.obj_id,
                       "expand":["metadata", "parentCollection",
                                 "parentCollectionList","parentCommunityList","bitstreams","all"],
                       "lastModified":" ",
                       "parentCollection":null,
                       "parentCollectionList":null,
                       "parentCommunityList":null,
                       "bitstreams":null,
                       "archived":"true",
                       "withdrawn":"false"
                      }
            cno = ses.post('%s/collection/%d/items'%(server, dspace_obj.parent_id),
                            headers=con_type, json=new_obj, cookies=ses_dic)
    else:
        print('Could not authenticate')

# função principal
def main():

    file_path = './test2/'
    directory = input("Select a directory to store the downloaded files:\n")
    if os.path.exists(file_path):
        for filename in glob.glob(os.path.join(file_path, '*.html')):
            local_file = open(filename, 'rb')
            soup = bs4.BeautifulSoup(local_file, 'lxml')
            parsing_module(filename, directory)
            local_file.close()
    else:
        print("Forneca um caminho valido!\n")
