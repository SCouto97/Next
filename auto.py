# -*- coding: utf-8 -*-
# @author: Samuel Andrade do Couto
# @email: samuelcoouto@hotmail.com
# @desc: Programa que realiza submissões automáticas dentro de um repositório
#        institucional que utiliza DSpace.
# @version: 0.5

import bs4, requests, os, sys, glob, errno, re, hashlib

# Convenções nesse programa para comunicação com a api REST:
# Por enquanto só criação para fazer os testes
# Key#:                  Operação:
#    1                    Criar uma comunidade
#    2                    Criar uma sub-comunidade
#    3                    Criar uma coleção
#    4                    Criar um item(lei, jurisprudência)
#    5                    Adicionar metadados ao item
#    6                    Adicionar bitstreams ao item

# Classe polimórfica para
#
class DspaceObject(object):
    def __init__(self, local, authority, name, date, obj_id, parent_id):
        self.local = local
        self.authority = authority
        self.name = name
        self.obj_id = obj_id
        self.parent_id = parent_id

class DspaceCommunity(DspaceObject):
    def __init__(self, obj_id, name):
        self.obj_id = obj_id
        self.name = name

class DspaceSubcommunity(DspaceObject):
    def __init__(self, obj_id, name, parent_id):
        self.obj_id = obj_id
        self.name = name
        self.parent_id = parent_id

class DspaceCollection(DspaceObject):
    def __init__(self, obj_id, name, parent_id):
        self.obj_id = obj_id
        self.name = name
        self.parent_id = parent_id

class DspaceItem(DspaceObject):
    def __init__(self, obj_id, name, parent_id):
        self.name = name
        self.obj_id = obj_id
        self.parent_id = parent_id

# @item_id inserido por conta da necessidade de informar o item a inserir o stream
class DspaceBitstream(DspaceObject):
    def __init__(self, name, extension, path, item_id):
        self.name = name
        self.extension = extension
        self.path = path
        self.item_id = item_id

    def bitstream_checksum(self):
        return checkSum(self.path)


class DspaceMetadata(DspaceObject):
    def __init__(self, title, desc, local, authority):
        self.title
        self.desc = desc
        self.local = local
        self.authority = authority

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
# @op indica o tipo de objeto do dspace a ser criado
def rest_aux(dspace_obj, op):
    null = None
    ses = requests.session()
    email = 'samuel.a.couto@gmail.com'
    password = 'Senha123'
    login = {'email' : email, 'password' : password}
    link = 'http://dev.jusbot.com.br/rest'
    r = ses.post(url='%s/login' % link, data=login)
    sessionID = ses.cookies['JSESSIONID']
    jses = 'JSESSIONID=%s' % sessionID
    con_type = {'content-type' : 'application/json'}
    if(r.status_code == 200):
        if(op == 1): # Criar uma comunidade
            com_obj = {
                       "uuid":dspace_obj.obj_id,
                       "name":dspace_obj.name,
                       "handle":"123456789/10213",
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
            ccom = ses.post(url='%s/communities' % link, headers=con_type,
                            json=com_obj)
        elif(op == 2): # Criar uma subcomunidade
            subcom_obj = {
                          "uuid":dspace_obj.obj_id,
                          "name":dspace_obj.name,
                          "handle":"123456789/10", # Número arbitrário
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
            sccom = ses.post(url='%s/communities/%d/communities'%(link, dspace_obj.parent_id),
                                  headers=con_type, json=subcom_obj)
        elif(op == 3): # Criar uma coleção
            col_obj = {
                       "uuid":dspace_obj.obj_id,
                       "name":dspace_obj.name,
                       "handle":"123456789/10214",
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
            ccol = ses.post(url='%s/communities/%s/collections'%(link, dspace_obj.parent_id),
                                 headers=con_type, json=col_obj)
        elif(op == 4): # Criar um item
            new_obj = {
                       "uuid":dspace_obj.obj_id,
                       "name":dspace_obj.name,
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
            cno = ses.post(url='%s/collections/%s/items'%(link, dspace_obj.parent_id),
                            headers=con_type, json=new_obj)
            id_soup = bs4.BeautifulSoup(cno.text, 'lxml')
            my_id = id_soup.find('uuid').text
            dspace_obj.obj_id = my_id
            rest_aux(dspace_obj, 5)

        elif(op == 5): # Adicionar metadados ao item
                       # Editar essa seção para incluir metadados no futuro
            new_metadata = [{
                            "key": "dc.title",
                            "value": dspace_obj.name,
                            "language": null
                           }]
            cnm = ses.put(url='%s/items/%s/metadata'%(link, dspace_obj.obj_id),
                           headers=con_type, json=new_metadata)
            if(cnm.status_code != 200):
                print('Erro ao incluir metadados')

        elif(op == 6):
            # condicional que faz a diferenciação dos formatos dos arquivos
            if(dspace_obj.extension == 'html'):
                item_format = "HTML"
                mimeType = "text/HTML"
            else:
                item_format = "Adobe PDF"
                mimeType = "application/pdf"
            new_bitstream = {
                             "uuid":123,
                             "name":dspace_obj.name,
                             "handle":'123456789/0',
                             "type":"bitstream",
                             "link":"/rest/bitstreams/123",
                             "expand":["parent","policies","all"],
                             "bundleName":"ORIGINAL",
                             "description":"",
                             "format":item_format,
                             "mimeType":mimeType,
                             "sizeBytes": int(os.path.getsize(dspace_obj.path)),
                             "parentObject":null,
                             "retrieveLink":"/bitstreams/47166/retrieve",
                             "checkSum":{"value": dspace_obj.bitstream_checksum(),
                                         "checkSumAlgorithm":"MD5"},
                             "sequenceId":1,
                             "policies":null
                            }
#            cnm = ses.post(url='%s/items/%s/bitstreams?name=%s.%s&description=description'%(link, dspace_obj.item_id, dspace_obj.name,
                                                                                #        dspace_obj.extension),headers=con_type, json=new_bitstream)
            assigned_uuid = DspaceRetrievebyName(dspace_obj.name+dspace_obj.extension, 'bitstreams')
            print(assigned_uuid)
            update_bits = ses.put(url='%s/bitstreams/%s/data'%(link, assigned_uuid), data=dspace_obj.path)
    else:
        print('Could not authenticate')
    return

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
    if(uuid):
        return uuid
    else:
        print('Não consegui achar tal objeto')
    return

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

# Versão de teste das funcionalidades
def DspaceRestUploader():
    print('Digite o tipo de objeto a ser criado:\n')
    print('1. Comunidade\n2. Subcomunidade\n3. Coleção\n4. Item\n5. Atualização de Metadados\n6. Bitstream\n')
    num_op = int(input('>> '))
    if(num_op == 1):
        iden = input('Digite o identificador da comunidade\n')
        nome = input('Digite o nome da comunidade\n')
        dspace = DspaceCommunity(iden, nome)
    elif(num_op == 2):
        iden = input('Digite o identificador da subcomunidade\n')
        nome = input('Digite o nome da subcomunidade\n')
        parent_name = input('Digite o nome da comunidade pai dessa subcomunidade\n')
        parent_id = DspaceRetrievebyName(parent_name, 'communities')
        dspace = DspaceSubcommunity(iden, nome, parent_id)
    elif(num_op == 3):
        iden = input('Digite o identificador da coleção\n')
        nome = input('Digite o nome da coleção\n')
        parent_name = input('Digite o nome da comunidade pai dessa coleção\n')
        parent_id = DspaceRetrievebyName(parent_name, 'communities')
        dspace = DspaceCollection(iden, nome, parent_id)
    elif(num_op == 4):
        iden = input('Digite o identificador do item\n')
        nome = input('Digite o nome do item\n')
        parent_name = input('Digite o nome da coleção o qual esse item pertence\n')
        parent_id = DspaceRetrievebyName(parent_name, 'collections')
        dspace = DspaceItem(iden, nome, parent_id)
    elif(num_op == 5):
        name = input('Digite o nome do bitstream\n')
        ext = input('Digite a extensão do bitstream\n')
        path = input('Digite o caminho para o bitstream\n')
        item_id = input('Digite o identificador do bitstream\n')
        dspace = DspaceBitstream(name, ext, path, item_id)
    elif(num_op == 6):
        title = input('Digite o titulo para o item\n')
        desc = input('Digite o abstract do artigo\n')
        local = input('Digite o local\n')
        authority = input('Digite a autoridade\n')
        dspace = DspaceMetadata(title, desc, local, authority)

    rest_aux(dspace, num_op)
    return

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

mock_object = DspaceBitstream(name='Acórdão São Paulo', extension='pdf', path='./down2/AC990QOSPSÃOPAULO.pdf', item_id='b6c206c0-d9c7-4c07-89e6-3fc22dc73891')
rest_aux(mock_object, 6)
