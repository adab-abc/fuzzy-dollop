# -*- coding: utf-8 -*-
"""
Created on Tue Aug  4 14:20:26 2026

@author: adabreo

Last Updated on Wed Aug 4 14:50 2026
"""
def parseWorkbook():
    import os
    import pandas as pd
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", None)

    while True:
        excelFile = input("Please enter data/template path:").strip().strip('"')
        if os.path.exists(excelFile):
            break
        print("\nFile not found. Please try again.")
    print("\nWorkbook found.")
    
    excelBook = pd.ExcelFile(excelFile)
    print("\nAvailable Worksheets: ")
    for sheet in excelBook.sheet_names:
        print(f" - {sheet}")
    while True: 
        worksheetName = input("\nEnter worksheet name: ").strip()
        if worksheetName in excelBook.sheet_names:
            break
        print("\nWorksheet not found. Please try again.")
    worksheet = pd.read_excel(excelFile, sheet_name=worksheetName, header=None)
    print(f"\nLoaded Worksheet: {worksheetName}")
    
    #Generalized Data Extraction Function
    def extractRegion(worksheet, concentrationRow, startRow, endRow):
        concentrations = list(worksheet.iloc[concentrationRow, 2:14])
        concentrations[9] = "Blank"
        concentrations[10] = "URC"
        concentrations[11] = "URD"
        data = worksheet.iloc[startRow:endRow+1, 2:14].copy()
        pairNames = list(worksheet.iloc[startRow:endRow+1,0])
        data.columns = concentrations
        data.index = pairNames
        return data
    
    REGIONS = {"IMG": {"concentrationRow":14, "startRow":16, "endRow":19}, 
               "AP": {"concentrationRow":25, "startRow":20, "endRow":23},
               "Sample1": {"concentrationRow":32, "startRow":34, "endRow":37}, 
               "Sample2": {"concentrationRow":43, "startRow":38, "endRow":41}, 
               }
    assayData={}
    for sampleName, region in REGIONS.items():
        assayData[sampleName] = extractRegion(worksheet, 
                                              concentrationRow = region["concentrationRow"], 
                                              startRow = region["startRow"], 
                                              endRow = region["endRow"])
    return assayData, excelFile, worksheetName
