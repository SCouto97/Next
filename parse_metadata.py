import bs4, re

def parse_file(path_to_file):
    filename = open(path_to_file, 'rb')
    soup = bs4.BeautifulSoup(filename, 'lxml')
    text = soup.text
    adv = re.compile('ADV.: .*')
    adv_list = adv.findall(text)
    recte = re.compile('RECTE.: .*')
    recte_list = recte.findall(text)
    recdo = re.compile('RECDO.: .*')
    recdo_list = re.findall(text)
    dj = re.compile('Julgamento: \d/\d/\d') 
