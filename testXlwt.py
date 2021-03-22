#coding=utf-8

import xlwt
import json
import datetime

excelfil = xlwt.Workbook()
ark = excelfil.add_sheet("Ark 1")

liste = [["A" ,"B" ,"C","D"] ,["1","2" ,"3","4"] ,["A" ,"B" ,"C","D"]]


for i in range(3):
    #print liste[i]
    for j in range(4):
        #print liste[i][j]
        ark.write(i,j, liste[i][j])



#excelfil.save("test.xls")

prisListeFil = u"C:\\Utvikling\\dev-python\\FakturaGrunnlag\\Prisliste.json"

with open(prisListeFil) as json_file:
    prisListe = json.load(json_file)



def hentPris(planType, takstAreal):
    prisPlanType = prisListe[planType][u"Pris_Daa"] #hent prisliste for gitt plantype

    prisPlanTypeFloatTuple= [(float(k),v) for k,v in prisPlanType.items()] #Gjør prislisten om til tuple med floatverdier

    prisPlanTypeFloatTuple.sort(key=lambda tup: tup[1]) # Sorterer prisliste stigende

    pris = None
    for i in prisPlanTypeFloatTuple: #Itererer prisliste, velger den første som takstareal er mindre enn.
        if takstAreal <= i[0]:
            pris =  i[1]
            break

    if pris == None: #Hvis arealet ikke er mindre enn noen, velg første som er pris for større enn..
        pris = prisPlanTypeFloatTuple[0][1]

    return (prisListe[planType][u"Domene"], pris)

nu = datetime.datetime.now()

filnavn = u"Fakturagrunnlag_" + nu.strftime('%d-%m-%y_%H:%M') + '.xls'

print filnavn