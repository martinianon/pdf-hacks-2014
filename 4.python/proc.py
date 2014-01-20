from bs4 import BeautifulSoup
import csv
import sys

archivo = sys.argv[1]
classNegrita = sys.argv[2]
classRegular = sys.argv[3]
anio = sys.argv[4]
meses = {
  'enero' : 1,
  'febrero' : 2,
  'marzo' : 3,
  'abril' : 4,
  'mayo' : 5,
  'junio' : 6,
  'julio' : 7,
  'agosto' : 8,
  'septiembre' : 9,
  'octubre' : 10,
  'noviembre' : 11,
  'diciembre' : 12
}


def parse_details(t):
  resp = {}
  details = t.split(',')

  if len(details):
    resp['nombre'] = details[0].replace('.','').strip().encode('utf-8')

  if len(details)>1:
    edad = details[1].strip().split(' ')[0].encode('utf-8')
    if edad.isdigit():
      resp['edad'] = edad


  resp['provincia'] = details[len(details)-1].replace('.','').strip().encode('utf-8')

  if len(details)>1:
    if details[len(details)-2] != details[1]:
      resp['localidad'] = details[len(details)-2].replace('.','').strip().encode('utf-8')

  return resp

def parse_fuente(t):
  resp = {}
  details = t.split('Fuente:')
  
  if len(details)>1:
      resp['descripcion'] = details[0].strip().encode('utf-8')
      resp['fuente'] = details[1].replace(':','').replace('s:','').strip().encode('utf-8')
  else:
      details = t.split('Fuentes:')
      if len(details)>1:
        resp['descripcion'] = details[0].strip().encode('utf-8')
        resp['fuente'] = details[1].replace(':','').replace('s:','').strip().encode('utf-8')
      else:
        resp['descripcion'] = t.encode('utf-8')
        resp['fuente'] = ''

  return resp

def parse_fecha(t,anio):
  resp = {}
  parts = t.split('.')

  if len(parts)>1:
    resp['vinculo'] = parts[1].strip().replace(')','').replace('(','').encode('utf-8')

  parts = parts[0].replace(')','').replace('(','').replace('.','').replace(',','').strip().split(' de ')

  resp['dia'] = parts[0].encode('utf-8')
  
  if len(parts)>1:
    try:
      resp['mes'] = meses[parts[1].replace('*','').replace(' ','').lower().strip()]

    except Exception, e:
      print parts

  resp['anio'] = anio
  return resp

with open(archivo, 'r') as content_file:
  content = content_file.read()
  parsed_html = BeautifulSoup(unicode(content, "utf-8"))

  ps = parsed_html.body.find_all('p')

  mujeres = []

  casos = []

  multiples = []

  #separo en casos
  mujer = None
  for p in ps:
    ix = p.find_all('span',attrs={'class':classNegrita})
    if len(ix) > 0:
      if ix[0].get_text().replace(')','').strip().isdigit():
        
        if mujer is not None:
          casos.append(mujer)

        #nuevo femicidio
        mujer = ''
        mujer = str(p)
    
    else:
      #mas detalles del mismo
      mujer = mujer + str(p)


  #obtengo detalles de los casos
  for i,m in enumerate(casos):
    mujer = {}
    multiple = False

    detalles = BeautifulSoup(unicode(m, "utf-8"))

    negritas = detalles.find_all('span',attrs={'class':classNegrita})

    regulares = detalles.find_all('span',attrs={'class':classRegular})

    mujer['id'] = negritas[0].get_text().replace(')','').strip()

    if regulares[0].get_text().strip() == 'y' or regulares[0].get_text().strip() == ',' :
      
      #ignore for now
      multiple = True
      multiples.append(detalles)

    else:
      #parse details
      detail = ''
      for i,d in enumerate(negritas):
        if i != 0:
          detail = detail + ' ' + d.get_text().strip()
      details = parse_details( detail )
      mujer.update(details)

      #parse fecha
      fecha = parse_fecha( regulares[0].get_text() , anio )
      mujer.update(fecha)

      #parse desc
      desc = ''
      for i,d in enumerate(regulares):
        if i != 0:
          desc = desc + d.get_text().strip() + ' '
      if desc[:1] == '.' or desc[:1] == ',' or desc[:1] == '"':
        desc = desc[1:]    
      
      details = parse_fuente(desc.strip())
      mujer.update(details)

      mujeres.append(mujer)

ordered_fieldnames = ['id','dia','mes','anio','nombre','edad','localidad','provincia','vinculo','fuente','descripcion']
with open('femi_'+anio+'.csv', 'wb') as f:
  dw = csv.DictWriter(f, delimiter=',', fieldnames=ordered_fieldnames)
  dw.writeheader()
  dw.writerows(mujeres)

with open('femi_multiples_'+anio+'.html', 'wb') as f:
  for m in multiples:
    f.write(str(m))

  print 'Casos :' + str(len(casos))

  print 'Procesados :' + str(len(mujeres))

  print 'Ambiguos :' + str(len(multiples))
