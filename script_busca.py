import requests
from bs4 import BeautifulSoup
import csv
import re

# Extrai os dados da página Web
def extract_data(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar o elemento "span" com a classe "acronym"
        url_herbariums = soup.find_all('span', class_='acronym')

        contacts = []
        #=----------------------------------------------------------------------=#
        for herbarium in url_herbariums:

            # Obter o URL do atributo "href" dentro da âncora "a"
            url = herbarium.a['href']

            # acrescentar o domínio ao URL
            url = 'https://specieslink.net' + url
                
            # Enviar uma solicitação HTTP para a página
            response = requests.get(url)

            # Variavel de Controle.
            listar = False

            # Verificar se a solicitação foi bem-sucedida
            if response.status_code == 200:
                print('Obtendo dados de: ' + url)

                # Analisar o conteúdo HTML da página
                soup = BeautifulSoup(response.text, 'html.parser')

                #=----------------------------------------------------------------------=#
                # Econtra dados da div_col7 que contem os dados dos provedores de dados.
                div_col7 = soup.find('div', class_='col-lg-7')

                universidade = ''
                depa_mus_inst = ''
                localizacao = ''
                municipio = ''
                uf = ''
                pais = ''

                if div_col7:
                    # Encontre o texto dentro da <h3>, sua sigle e descrição
                    h3_text = div_col7.find('h3').get_text(strip=True)
                    fornecedor_sigla = h3_text.split('-')[0].strip()
                    fornecedor_nome = h3_text.split('-')[1].strip()

                    # Lógica que verifica se é um Herbário
                    if re.match(r'.*Herbário.*', fornecedor_nome):
                        listar = True
                    
                    if listar:
                        # Encontre todos os elementos <br> dentro da <div>
                        br_elements = div_col7.find_all('br')
                        for br in br_elements:
                            br_text = br.next_sibling.strip()
                            
                            if re.match(r'[A-Z]+(?:\s-\s[A-Za-z\s]+)+', br_text):
                                universidade = br_text # não é usado por hora 
                            elif re.match(r'([\w\s]+) - ([A-Z]{2}|\w+) - ([\w\s]+)', br_text):
                                localizacao = br_text
                            else:
                                depa_mus_inst = br_text # não é usado por hora

                        # Separa a localização em municipio, uf e País
                        localizacao = localizacao.split('-')
                        if len(localizacao) >= 3:
                            municipio = localizacao[0]
                            uf = localizacao[1]
                            pais = localizacao[2]
                    
                if listar:
                    #=----------------------------------------------------------------------=#
                    # Condições para utilização dos dados
                    cond_of_utilization = soup.find('h4', string='Condições para utilização dos dados')

                    cons = ''
                    if cond_of_utilization:
                        cons = cond_of_utilization.find_next('p').get_text(strip=True)

                    #=----------------------------------------------------------------------=#
                    # Encontrar a tag <h4>Como citar</h4>
                    reference_heading = soup.find('h4', string='Como citar')

                    referencing = ''
                    if reference_heading:
                        referencing = reference_heading.find_next('p').get_text(strip=True)

                    #=----------------------------------------------------------------------=#
                    # Número de Registros
                    register_headings = soup.find('h4', string='Número de registros')

                    reg_total = ''  
                    reg_online = ''
                    reg_georef = ''
                    reg_img = ''
    
                    if register_headings:
                        # Encontre a próxima <div class="row"> após o <h4>
                        div_row = register_headings.find_next('div', class_='row')
                        if div_row:
                            # Encontre todos os elementos <div> dentro da próxima <div class="row">
                            divs = div_row.find_all('div', class_='col-md-3 text-nowrap')
                            for div in divs:
                                # Extraia o rótulo e o valor
                                label = div.find('span', class_='label').text.strip()
                                if label == 'Total:':
                                    reg_total = div.text.strip().replace(label, '').replace('.', '')
                                elif label == 'Online:':
                                    reg_online = div.text.strip().replace(label, '').replace('.', '')
                                elif label == 'Georreferenciados:':
                                    if div.find('a'):
                                        reg_georef = div.find('a').text.strip().replace('.', '')
                                    else: # quando não tem link para os georreferenciados div a não existe
                                        reg_georef = 0
                                elif label == 'Com Imagens:':
                                    reg_img = div.text.strip().replace(label, '').replace('.', '')
                                    
                    #=----------------------------------------------------------------------=#
                    # Encontrar a tag <h4>Contatos</h4>
                    contacts_heading = soup.find('h4', string='Contatos')

                    cargo = ''
                    nome = ''
                    email = ''

                    # Navegar pelos irmãos da tag <h4>Contatos</h4>
                    if contacts_heading:
                        for sibling in contacts_heading.find_next_siblings():
                            # Se for uma tag <span> com a classe "label", é um novo cargo
                            if sibling.name == 'span' and 'label' in sibling.get('class', []):
                                cargo = sibling.text.strip().replace(':', '')
                            # Se for uma tag <span> com a classe "ml-3", é um nome
                            if sibling.name == 'span' and 'ml-3' in sibling.get('class', []):
                                nome = sibling.text.strip()
                            # Se for uma tag <a> é um e-mail
                            if sibling.name == 'a':
                                email = sibling.get('href', '').replace('mailto:', '')
                        
                            if cargo != '' and nome != '' and email != '':
                                contacts.append({'Cargo': cargo, 'Nome': nome, 'Email': email})
                                cargo = ''
                                nome = ''
                                email = ''

                    #=----------------------------------------------------------------------=#
                    # Adiciona os dados a lista
                    for contact in contacts:
                        herbarium_data.append({'url': url, 'Sigla': fornecedor_sigla, 'Fornecedor': fornecedor_nome, 
                                               #'Universidade': universidade, 'Resposável': depa_mus_inst, 
                                               'Municipio': municipio, 'UF': uf, 'Pais': pais, 
                                               'Condição para utilização': cons, 'Como Citar': referencing, 
                                               'Total de Registros': reg_total, 'Registros Online': reg_online, 'Registros Georreferenciados': reg_georef, 'Registros com Imagens': reg_img,
                                               'Cargo': contact['Cargo'], 'Nome': contact['Nome'], 'Email': contact['Email']})
                    contacts = []
                #=----------------------------------------------------------------------=#
        #endfor
        #=----------------------------------------------------------------------=#
        return herbarium_data
    else:
        print('Falha ao obter a página: ' + url)
        return []

# URL da primeira página
base_url = 'https://specieslink.net/col/'
page_number = 1

herbarium_data = []

while True:
    # Cria a URL da página atual
    current_url = f'{base_url}?page={page_number}'

    # Extraia dados da url
    page_data = extract_data(current_url)

    # Se não houver mais dados na página, saia do loop
    if not page_data:
        break

    # Aumente o número da página para ir para a próxima página
    page_number += 1

    # Controle extração
    if page_number >= 22:
        break

# Gera CSV
print('Gerando arquivo CSV...')
with open('herbarios.csv', mode='w', newline='', encoding='utf-8') as csv_file:
    # Inicializar o escritor CSV
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['URL', 'Sigla', 'Fornecedor', 
                         #'Universidade', 'Resposável', 
                         'Município', 'UF', 'País', 
                         'Condição para utilização', 'Como Citar', 
                         'Total de Registros', 'Registros Online', 'Registros Georreferenciados', 'Registros com Imagens',
                         'Cargo', 'Nome', 'Email'])
    for herbarium in herbarium_data:
        csv_writer.writerow([herbarium['url'], herbarium['Sigla'] ,herbarium['Fornecedor'], 
                             #herbarium['Universidade'], herbarium['Resposável'], 
                             herbarium['Municipio'], herbarium['UF'], herbarium['Pais'], 
                             herbarium['Condição para utilização'], herbarium['Como Citar'], 
                             herbarium['Total de Registros'], herbarium['Registros Online'], herbarium['Registros Georreferenciados'], herbarium['Registros com Imagens'],
                             herbarium['Cargo'], herbarium['Nome'], herbarium['Email']])

print('Dados salvos no arquivo herbarios.csv')