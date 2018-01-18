import bs4, re

def parse_file(path_to_file):
    filename = open(path_to_file, 'rb')
    soup = bs4.BeautifulSoup(filename, 'lxml')
    adv_pattern = re.compile('ADV.: ')
