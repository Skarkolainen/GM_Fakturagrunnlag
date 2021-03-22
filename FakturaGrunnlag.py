#coding=utf-8

import arcpy
import os
import xlwt
import json

# ta inn Eiendom og bestand, direktekobling, ikke bruk lag i mxd ?

# ta inn verktøyparametere
    # Hovednr-liste

runAsTool = True

if runAsTool == True:
    gdb = arcpy.GetParameterAsText(0)
    hovednummere = arcpy.GetParameterAsText(1)
    ispeddArealGrense = int(arcpy.GetParameterAsText(2))
    maxAndelIspedd = int(arcpy.GetParameterAsText(3))
    utfil = arcpy.GetParameterAsText(4)
    prisListeFil = ""

    #osv feks kun Plantype over null, utfil
else:
    gdb = r"C:\Utvikling\dev-python\testdata\Testdata2021.gdb"
    hovednummere = '01180006600010000,01180006600020000,01180006700040000,01180006700030000,01180006700050000'
    #hovednummere = "01180000500010000"
    ispeddArealGrense = 10
    maxAndelIspedd = 10
    prisListeFil = r"C:\Utvikling\dev-python\FakturaGrunnlag\Prisliste.json"

#initier eiendomslag
arcpy.env.workspace = gdb

dataset = arcpy.ListDatasets("*Topologi_valideres")[0]

fcs = arcpy.ListFeatureClasses(feature_dataset = dataset)
for fc in fcs:
    #arcpy.AddMessage(str(fc))
    if fc.endswith("EIENDOM"):
        EiendomFC = str(os.path.join(gdb, dataset + "\\" + fc))
    if fc.endswith("BESTAND"):
        BestandFC = os.path.join(gdb, dataset + "\\" + fc)

skogeierTABELL = os.path.join(gdb, u'SKOGEIER')

print_debug = True



# Lag eiendomsobjekt: holder variabler fra bestand, eiendom og skogeier
    #har egne funksjoner for å hente info fra bestand, eiendom og skogeier
    #Har egen toString metode, som skriver linje som passer inn til excel-arket fakturagrunnlag.
    #TODO kontrollmetoder som sjekker, feks at bestandsarealet er likt eiendomsarealet, kan avdekke topologi-feil.

#Hent prisliste

with open(prisListeFil) as json_file:
    prisListe = json.load(prisListeFil)

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


def eiendomsAreal(hovednr):
    felter = ['AREAL_DAA', 'Shape_Area']
    uttrykk = "HOVEDNR = '" + str(hovednr) + "'"

    with arcpy.da.SearchCursor(EiendomFC, felter, where_clause=uttrykk) as cursor:
        sumAreal = 0
        for row in cursor:
            sumAreal += row[1]

        return sumAreal / 1000

def bestandsAreal(hovednr):
    felter = ['MARKSLAG','AREALBRUTTO','AREALPROD','AREALUPROD']
    uttrykk = "HOVEDNR = '" + str(hovednr) + "'"

    with arcpy.da.SearchCursor(BestandFC, felter, where_clause=uttrykk) as cursor:
        sumBestandsAreal = 0
        sumProdAreal = 0
        sumUprodAreal = 0
        sumIspeddAreal = 0

        for row in cursor:
            sumBestandsAreal += row[1]
            sumProdAreal += row[2]
            sumUprodAreal += row[3]

            #Test for Ispedd
            if row[0]> 29 and row[0] is not 45 and row[1] <= ispeddArealGrense:
                sumIspeddAreal += row[1]



        # Beregner maksimum lovlig ispedd areal, og setter sumIspeddAreal til denne hvis faktisk ispedd areal overstiger
        maxAndel = float(maxAndelIspedd) / 100

        maxIspeddAreal = sumProdAreal * maxAndel

        if sumIspeddAreal > maxIspeddAreal:
            sumIspeddAreal = maxIspeddAreal

        sumTakstAreal = sumProdAreal + sumIspeddAreal

        return (sumBestandsAreal,sumProdAreal, sumUprodAreal, sumIspeddAreal,sumTakstAreal)

def skogeierVariabler(hovednr):
    felter = ['FORNAVN','ETTERNAVN','ADRESSE','POSTNR','POSTSTED','PLANTYPE']
    uttrykk = "HOVEDNR = '" + str(hovednr) + "'"

    with arcpy.da.SearchCursor(skogeierTABELL, felter,
                           where_clause=uttrykk) as cursor:
        for row in cursor:
            fornavn = row[0]
            etternavn = row[1]
            adresse = row[2]
            postnr = row[3]
            poststed = row[4]
            plantype = row[5]

    return (fornavn, etternavn, adresse, postnr, poststed, plantype)


class Eiendom:
    """Felles klasse for alle eiendommer"""
    antallEiendommer = 0

    def __init__(self, hovednr):
        self.hovednr = hovednr

        #Populer bestandsdata
        bestandsarealer = bestandsAreal(self.hovednr)

        self.sumBestandsAreal = bestandsarealer[0]
        self.sumProdAreal = bestandsarealer[1]
        self.sumUprodAreal = bestandsarealer[2]
        self.sumIspeddAreal = bestandsarealer[3]
        self.sumTakstAreal = bestandsarealer[4]

        #Populer eiendomsdata
        self.totaltArealEiendom = eiendomsAreal(self.hovednr)

        #Hent skogeierdata
        skogeier = skogeierVariabler(self.hovednr)

        self.fornavn = skogeier[0]
        self.etternavn = skogeier[1]
        self.adresse = skogeier[2]
        self.postnr = skogeier[3]
        self.poststed = skogeier[4]
        self.plantype = skogeier[5]

        #Teller antall eiendomsobjekter
        Eiendom.antallEiendommer += 1



    def arealerToString(self):
        return str(self.hovednr) + "\n sum Bestandsareal: " + str(self.sumBestandsAreal) +  "\n sum Prod areal: " + str(self.sumProdAreal) +\
               "\n sumUprodAreal: " + str(self.sumUprodAreal) + "\n sum Ispedd: " + str(self.sumIspeddAreal) + "\n sumTakstAreal: "+\
               str(self.sumTakstAreal) + "\n totaltArealEiendom: " + str(self.totaltArealEiendom)

    def toExcelRow(self):
        return [self.hovednr, self.fornavn, self.etternavn, self.adresse, self.postnr, self.poststed, self.plantype,
                self.sumBestandsAreal, self.sumProdAreal, self.sumIspeddAreal, self.sumTakstAreal]



# Iterer inn-hovednr, opprett eiendomsobjekter
    #Konstrueres med hovednr, kanskje også metoder for å hente data kalles ved konstruksjon.

alleEiendommer = []

innHovednr = hovednummere.replace(" ","")
HNR_set = set(innHovednr.split(','))
HNR_set = sorted(list(HNR_set))

for i in HNR_set:
    alleEiendommer.append( Eiendom(i) )

#print "Antall eiendommer: " + str(Eiendom.antallEiendommer)

alleExcelLinjer = []
for i in alleEiendommer:
    alleExcelLinjer.append(i.toExcelRow())


#Når eiendomsobjekter er konstruert, itererer dem, kall toString og skriv det til excel.

excelfil = xlwt.Workbook()
ark = excelfil.add_sheet("Ark 1")

#liste = [["A" ,"B" ,"C","D"] ,["1" ,"2" ,"3","4"] ,["A" ,"B" ,"C","D"]]
overskrifter = ["HOVEDNUMMER","Fornavn","Etternavn","Adresse","Postnummer","Poststed","Plantype","Totalt Areal",
                "Produktivt Areal","Uprod.Ispedd Areal", "Takstareal"]

for i in range(len(overskrifter)):
    ark.write(0,i, overskrifter[i])

for i in range(len(alleExcelLinjer)):
    #print liste[i]
    print ("I: " + str(i))
    for j in range(len(overskrifter)):
        #print liste[i][j]
        ark.write(i+1,j, alleExcelLinjer[i][j])



excelfil.save(utfil +"/tester.xls")





# Tøm Eiendom og fc fra minne

#Etterhvert: Implementer total beregning, med tilskuddsprosent, prismatrise ift. produkt osv.
    # Tilskuddsprosent
    # Grunnpris
    # prismatrise, som fil?

