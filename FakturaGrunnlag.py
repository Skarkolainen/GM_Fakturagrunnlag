#coding=utf-8

import arcpy
import os
# ta inn Eiendom og bestand, direktekobling, ikke bruk lag i mxd ?

# ta inn verktøyparametere
    # Hovednr-liste

runAsTool = False

if runAsTool == True:
    gdb = arcpy.GetParameterAsText(0)
    #osv feks kun Plantype over null, utfil
else:
    gdb = r"C:\Utvikling\dev-python\testdata\Testdata2021.gdb"
    hovednummere = '01180006600010000,01180006600020000,01180006700040000,01180006700030000,01180006700050000'
    #hovednummere = "01180000500010000"
    ispeddArealGrense = 10
    maxAndelIspedd = 10

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


print_debug = True



# Lag eiendomsobjekt: holder variabler fra bestand, eiendom og skogeier
    #har egne funksjoner for å hente info fra bestand, eiendom og skogeier
    #Har egen toString metode, som skriver linje som passer inn til excel-arket fakturagrunnlag.
    #Har kontrollmetoder som sjekker, feks at bestandsarealet er likt eiendomsarealet, kan avdekke topologi-feil.
def eiendomsAreal(hovednr):
    felter = ['AREAL_DAA', 'Shape_Area']
    uttrykk = "HOVEDNR = '" + str(hovednr) + "'"

    with arcpy.da.SearchCursor(EiendomFC, felter, where_clause=uttrykk) as cursor:
        sumAreal = 0
        for row in cursor:
            sumAreal += row[1]

        return sumAreal / 1000

def bestandsAreal(hovednr):
    felter = ['MARKSLAG','AREALBRUTTO','AREALPROD','AREALUPROD', 'Shape_Area']
    uttrykk = "HOVEDNR = '" + str(hovednr) + "'"

    with arcpy.da.SearchCursor(BestandFC, felter, where_clause=uttrykk) as cursor:
        sumBestandsAreal = 0
        sumProdAreal = 0
        sumUprodAreal = 0
        sumIspeddAreal = 0
        sumTakstAreal = 0

        for row in cursor:
            sumBestandsAreal += row[1]
            sumProdAreal += row[2]
            sumUprodAreal += row[3]

            #Test for Ispedd
            if row[0]> 29 and row[0] is not 45 and row[1] <= ispeddArealGrense:
                sumIspeddAreal += row[1]


        maxIspeddAreal = sumProdAreal * (maxAndelIspedd / 100)
        if sumIspeddAreal > maxIspeddAreal:
            sumIspeddAreal = maxIspeddAreal

        return (sumBestandsAreal,sumProdAreal, sumUprodAreal, sumIspeddAreal,sumTakstAreal)








class Eiendom:
    "Felles klasse for alle eiendommer"
    antallEiendommer = 0

    def __init__(self, hovednr):
        self.hovednr = hovednr

        bestandsarealer = bestandsAreal(self.hovednr)

        self.sumBestandsAreal = bestandsarealer[0]
        self.sumProdAreal = bestandsarealer[1]
        self.sumUprodAreal = bestandsarealer[2]
        self.sumIspeddAreal = bestandsarealer[3]
        self.sumTakstAreal = bestandsarealer[4]

        self.totaltArealEiendom = eiendomsAreal(self.hovednr)

        Eiendom.antallEiendommer += 1



    def hnrToString(self):
        return str(self.hovednr)



# Iterer inn-hovednr, opprett eiendomsobjekter
    #Konstrueres med hovednr, kanskje også metoder for å hente data kalles ved konstruksjon.

alleEindommer = []

innHovednr = hovednummere.replace(" ","")
HNR_set = set(innHovednr.split(','))
HNR_set = sorted(list(HNR_set))

for i in HNR_set:
    alleEindommer.append( Eiendom(i) )

print Eiendom.antallEiendommer

for i in alleEindommer:
    print i.hnrToString()
    print i.sumBestandsAreal
    print i.sumProdAreal
    print i.sumUprodAreal

#Når eiendomsobjekter er konstruert, itererer dem, kall toString og skriv det til excel.



# Tøm Eiendom og fc fra minne

#Etterhvert: Implementer total beregning, med tilskuddsprosent, prismatrise ift. produkt osv.
    # Tilskuddsprosent
    # Grunnpris
    # prismatrise, som fil?

