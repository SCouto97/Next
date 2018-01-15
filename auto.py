# -*- coding: utf-8 -*-
# #!/usr/bin/env/python3.5
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.6

import bs4, requests, os, sys, glob, errno, re, hashlib

'''
 Convenções nesse programa para comunicação com a api REST:
 Por enquanto só criação para fazer os testes
 Key#:                  Operação:
    1                    Criar uma comunidade
    2                    Criar uma sub-comunidade
    3                    Criar uma coleção
    4                    Criar um item(lei, jurisprudência)
    5                    Adicionar metadados ao item
    6                    Adicionar bitstreams ao item
'''
'''
  Workflow do programa:
  Cria as comunidades com base nos tribunais;
  Cria as coleções: Leis e Jurisprudências para cada tribunal;
  Cria itens e os popula com base nos arquivos
'''
class LexmlObject(object):
    def __init__(self, title, authority, date, local, desc):
        self.title = title
        self.authority = authority
        self.date = date
        self.desc = desc

# função de parsing coleta atributos sobre os metadados e chama a função de baixar
# as urls contidas nesses dados
def parsing_module(my_file):
    print("Parsing file %s...\n" % (my_file))
    local_file = open(my_file, 'rb')
    soup = bs4.BeautifulSoup(local_file, 'lxml')
    desc_elems = soup.findAll('div', {'class' : 'result_col2'})
    localidade = desc_elems[0].text
    autoridade = desc_elems[1].text
    titulo = desc_elems[2].text
    data = desc_elems[3].text
    desc = desc_elems[4].text
    lex_obj = LexmlObject(title=titulo, authority=autoridade, date=data, local=localidade, desc=desc)
    ext_elems = soup.findAll('span', {'class' : 'noprint'})
    l = []
    for e in ext_elems:
        r = re.findall('doc', e.text)
        if(len(r) != 0):
            l.append(r)
    if(len(l) != 0):
        lex_obj.extension = 'doc'
    else:
        lex_obj.extension = 'pdf'
    url_elems = soup.findAll('a', {'class' : 'noprint', 'href' : True})
    refs = [] # cria uma lista de referências vazia
    for elem in url_elems:
        refs.append(elem['href'])
    valid_urls = [x for x in refs if "lex" not in x]
    valid_urls = [x for x in valid_urls if "legislacao" not in x]
    lex_obj.links = []
    for url in valid_urls:
        lex_obj.links.append(url)
    return lex_obj
#        download_module(my_url=url, title=titulo, downl_path=downl_dir, ext=extension)

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

    path_to_file = '%s/%s.%s' % (directory, local_title, ext)
    with open(path_to_file, 'wb') as f:
        f.write(my_request.content)
    return path_to_file

def checkSum(filename):
    checksum_md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum_md5.update(chunk)
    return checksum_md5.hexdigest()


# função que obtém os arquivos de metadados dos sites do lexml
def crawl_sitemap():
    url = input('escreva o sitemap que deseja baixar:\n');
    sitemap = requests.get(url).text
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    count = 0
    extension = 'html'
    for link in links:
        count += 1
        sep = link.split('/')
        nome = sep[4]
        download_module(my_url=link, downl_path='sitemap_data', title=nome, ext=extension)
    print('Number of pages crawled: %d\n' % count)

def getExtension(filename):
    parts = filename.split('.')
    return parts[-1]

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
        print('Old file name: %s' % filename)
        os.rename(filename, filename_new)
        print('Renamed to: %s' % filename_new)

def DspaceRetrievebyName(name, obj_type):
    se = requests.session()
    jus_url = 'http://dev.jusbot.com.br/rest'
    object_json = se.get(url='%s/%s'%(jus_url, obj_type)).json()
    uuid = None
    if(object_json != []):
        for obj in object_json:
            if(obj['name'] == name):
                uuid = obj['uuid']
                break
    return uuid

def DspaceRestRemoval():
    login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
    url = 'http://dev.jusbot.com.br/rest'
    delete_session = requests.session()
    login = requests.post(url='%s/login'%url, data=login_info)
    print('Digite o tipo de objeto que deseja remover:')
    print('1. Comunidade\n2. Subcomunidade\n3. Coleção\n4. Item\n5. Bitstream\n6. Retornar')
    num_op = int(input('>> '))
    if(num_op != 6):
        print('Digite o nome do objeto:')
        nome = input('>> ')
    if(num_op == 1):
        uuid = DspaceRetrievebyName(nome, 'communities')
        if(uuid):
            delete_session.delete(url='%s/communities/%s' % (url, uuid))
            print('Deleting: %s/communities/%s' % (url, uuid))
    if(num_op == 2):
        uuid = DsapceRetrievebyName(nome, 'communities')
        if(uuid):
            delete_session.delete(url='%s/communities/%s' % (url, uuid))
    if(num_op == 3):
        uuid = DspaceRetrievebyName(nome, 'collections')
        if(uuid):
            delete_session.delete(url='%s/collections/%s' % (url, uuid))
    if(num_op == 4):
        uuid = DspaceRetrievebyName(nome, 'items')
        if(uuid):
            delete_session.delete(url='%s/collections/%s' % (url, uuid))
    if(num_op == 5):
        uuid = DspaceRetrievebyName(nome, 'bitstreams')
        if(uuid):
            delete_session.delete(url='%s/collections/%s' % (url, uuid))
    if(num_op == 6):
        os.system('exit')

# Cria as comunidades conforme o Workflow
def DspaceCommunityCreator(name):
    com_ses = requests.session()
    link = 'http://dev.jusbot.com.br/rest'
    community_list = com_ses.get('%s/communities'%link).json()
    found = 0
    for com in community_list:
        if(com['name'] == name):
            print('Com: Comunidade já existe')
            found = 1
            break
    if(not found):
        null = None
        con_type = {'content-type' : 'application/json'}
        login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
        login = com_ses.post(url='%s/login'%link, data=login_info)
        com_obj = {
                   "uuid":1,
                   "name":name,
                   "handle":"123456789/10213",
                   "type":"community",
                   "link":"/rest/communities/1",
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
        ccom = com_ses.post(url='%s/communities' % link, headers=con_type, json=com_obj)
        print('Com: Comunidade {name} criada com sucesso'.format(name=name))
    else:
        return

def DspaceSubcommunityCreator(name, com_name):
    subcom_ses = requests.session()
    link = 'http://dev.jusbot.com.br/rest'
    com_id = DspaceRetrievebyName(com_name, 'communities/top-communities')
    subcom_request = subcom_ses.get('%s/communities/%s/communities'%(link,com_id))
    if(subcom_request.status_code == 200):
        found = False
        subcom_list = subcom_request.json()
        for sc in subcom_list:
            if(sc['name'] == name):
                print('Subc: A comunidade {com_name} já possui uma subcomunidade chamada {name}'.format(
                       com_name=com_name, name=name))
                found = True
                break
        if(not found):
            null = None
            con_type = {'content-type' : 'application/json'}
            login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
            login = subcom_ses.post(url='%s/login'%link, data=login_info)
            subcom_id = DspaceRetrievebyName(name, 'communities')
            subcom_obj = {
                       "uuid":1,
                       "name":name,
                       "handle":"123456789/10213",
                       "type":"community",
                       "link":"/rest/communities/1",
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
            csubcom = subcom_ses.post(url='%s/communities/%s/communities'%(link, com_id),
                                 headers=con_type, json=subcom_obj)
            if(csubcom.status_code == 200):
                print('Subc: Subcomunidade {name} criada com sucesso!'.format(name=name))
            else:
                return
        else:
            return
    else:
        print('Subc: Não existe comunidade nomeada {com_name}'.format(com_name=com_name))

# TODO: Validar existência de comunidade
def DspaceCollectionCreator(name, com_name):
    col_ses = requests.session()
    link = 'http://dev.jusbot.com.br/rest'
    com_id = DspaceRetrievebyName(com_name, 'communities')
    col_request = col_ses.get('%s/communities/%s/collections'%(link,com_id))
    print(com_name)
    if(col_request.status_code == 200):
        found = 0
        collections_list = col_request.json()
        for col in collections_list:
            if(col['name'] == name):
                print('Col: A comunidade {com_name} já possui uma coleção chamada {name}'.format(
                       com_name=com_name, name=name))
                found = 1
                break
        if(not found):
            null = None
            con_type = {'content-type' : 'application/json'}
            login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
            login = col_ses.post(url='%s/login'%link, data=login_info)
            col_obj = {
                       "uuid":1,
                       "name":name,
                       "handle":"123456789/10214",
                       "type":"collection",
                       "link":"/rest/collections/1",
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
            ccol = col_ses.post(url='%s/communities/%s/collections'%(link, com_id),
                                 headers=con_type, json=col_obj)
            print('Col: Coleção {name} criada com sucesso!'.format(name=name))
        else:
            return
    else:
        print('Col: Não existe comunidade nomeada {com_name}'.format(com_name=com_name))

# Criar um item pode acabar se tornando algo custoso dependendo do escopo da busca
def DspaceItemCreator(name, com_name, col_name, desc):
    ses_item = requests.session()
    link = 'http://dev.jusbot.com.br/rest'
    com_id = DspaceRetrievebyName(com_name, 'communities')
    collections_request = ses_item.get('%s/communities/%s/collections'%(link, com_id))
    if(collections_request.status_code == 200):
        col_id = DspaceRetrievebyName(col_name, 'communities/%s/collections'%com_id)
        item_request = ses_item.get('%s/collections/%s/items'%(link, col_id))
        if(item_request.status_code == 200):
            found  = 0
            item_list = item_request.json()
            for item in item_list:
                if(item['name'] == name):
                    print('Item: Já existe um item {name} na coleção {col}'.format(name=name, col=col_name))
                    found = 1
                    break
            if(not found):
                null = None
                login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
                login = ses_item.post(url='%s/login'%link, data=login_info)
                con_type = {'content-type' : 'application/json'}
                new_item = {
                           "uuid":1,
                           "name":null,
                           "handle":"123456789/13470",
                           "type":"item",
                           "link":"/rest/items/1",
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
                cnit = ses_item.post(url='%s/collections/%s/items'%(link, col_id),
                                headers=con_type, json=new_item)
                id_soup = bs4.BeautifulSoup(cnit.text, 'lxml')
                item_id = id_soup.find('uuid').text
    #---------------------------------------------------------------------------------------------------
                new_metadata = [{
                                "key": "dc.title",
                                "value": name,
                                "language": "pt_BR"
                               },
                               {
                                "key": "dc.description.abstract",
                                "value": desc,
                                "language": "pt_BR"
                               }]
    #---------------------------------------------------------------------------------------------------
                cnm = ses_item.put(url='%s/items/%s/metadata'%(link, item_id),
                                headers=con_type, json=new_metadata)
                if(cnm.status_code != 200):
                    print('Mtd: Erro ao incluir metadados')
        else:
            print('Item: Não existe coleção nomeada {name}'.format(name=col_name))
        return
    else:
        print('Item: Não existe comunidade nomeada {name}'.format(name=com_name))

def DspaceUploadBitstream(name, path_to_file, com_name, col_name, item_name):
    bit_ses = requests.session()
    link = 'http://dev.jusbot.com.br/rest'
    com_id = DspaceRetrievebyName(com_name, 'communities')
    if(com_id):
        col_id = DspaceRetrievebyName(col_name, 'communities/%s/collections'%com_id)
        if(col_id):
            item_id = DspaceRetrievebyName(item_name, 'collections/%s/items'%col_id)
            if(item_id):
                found = False
                bitstream_list = bit_ses.get('%s/items/%s/bitstreams'%(link, item_id)).json()
                for bit in bitstream_list:
                    if(bit['name'] == name):
                        print('Bts: O item {name1} já possui um bitstream com nome {name2}'.format(name1=item_name, name2=name))
                        found = True
                        break
                if(not found):
                    null = None
                    login_info = {'email' : 'samuel.a.couto@gmail.com', 'password' : 'Senha123'}
                    login = bit_ses.post(url='%s/login'%link, data=login_info)
                    con_type = {'content-type' : 'application/json'}
                    extension = getExtension(path_to_file)
                    if(extension == 'html'):
                        item_format = "HTML"
                        mimeType = "text/HTML"
                    else:
                        item_format = "Adobe PDF"
                        mimeType = "application/pdf"
                        new_bitstream = {
                                     "uuid":123,
                                     "name":name,
                                     "handle":'123456789/0',
                                     "type":"bitstream",
                                     "link":"/rest/bitstreams/123",
                                     "expand":["parent","policies","all"],
                                     "bundleName":"ORIGINAL",
                                     "description":"",
                                     "format":item_format,
                                     "mimeType":mimeType,
                                     "sizeBytes": int(os.path.getsize(path_to_file)),
                                     "parentObject":null,
                                     "retrieveLink":"/bitstreams/47166/retrieve",
                                     "checkSum":{"value": checkSum(path_to_file),
                                                 "checkSumAlgorithm":"MD5"},
                                     "sequenceId":1,
                                     "policies":null
                                    }
                        filename = {name : open(path_to_file, 'rb')}
                        cnm = bit_ses.post(url='%s/items/%s/bitstreams?name=%s.%s&description=description'%(link, item_id, name, extension),
                                                                                      headers=con_type, json=new_bitstream, files=filename)
                else:
                    return
            else:
                print('Bts: Não consegui achar o item {name}'.format(name=item_name))
        else:
            print('Bts: Não consegui achar a coleção {name}'.format(name=col_name))
    else:
        print('Bts: Não consegui achar a comunidade {name}'.format(name=com_name))
        return

def main_workflow():
    path_to_files = './testfolder/'
    if os.path.exists(path_to_files):
        for filename in glob.glob(os.path.join(path_to_files, '*')):
            local_obj = parsing_module(filename)
            downl_dir = './a'
            index = 0
            bitstream_list = []
            for link in local_obj.links:
                aux = download_module(my_url=link, title=local_obj.title, downl_path=downl_dir, ext=local_obj.extension)
                bitstream_list.append(aux)
            name_list = local_obj.authority.split('.')
            name_list[1] = name_list[1].lstrip()
            DspaceCommunityCreator(name_list[0])
            if(len(name_list) > 1):
                DspaceSubcommunityCreator(name=name_list[1], com_name=name_list[0])
                index = 1
            else:
                index = 0
            DspaceCollectionCreator('Leis', name_list[index])
            DspaceItemCreator(local_obj.title, name_list[index], 'Leis', local_obj.desc)
            DspaceUploadBitstream('original', bitstream_list[0], name_list[index], 'Leis', local_obj.title)
    else:
        print("Forneça um caminho válido!\n")

main_workflow()
