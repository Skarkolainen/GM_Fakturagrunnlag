import xlwt



excelfil = xlwt.Workbook()
ark = excelfil.add_sheet("Ark 1")

liste = [["A" ,"B" ,"C","D"] ,["1" ,"2" ,"3","4"] ,["A" ,"B" ,"C","D"]]


for i in range(3):
    #print liste[i]
    for j in range(4):
        #print liste[i][j]
        ark.write(i,j, liste[i][j])



excelfil.save("test.xls")