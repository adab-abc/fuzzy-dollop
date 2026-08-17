# -*- coding: utf-8 -*-
"""
Parser for local execution and Streamlit deployment
"""

import pandas as pd


def parseWorkbook(workbookPath, worksheetName=None):

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)
    pd.set_option("display.max_colwidth", None)

    excelBook = pd.ExcelFile(workbookPath)

    if worksheetName is None:

        worksheetName = excelBook.sheet_names[0]

    worksheet = pd.read_excel(
        workbookPath,
        sheet_name=worksheetName,
        header=None
    )

    print(f"\nLoaded Worksheet: {worksheetName}")

    def extractRegion(
        worksheet,
        concentrationRow,
        startRow,
        endRow
    ):

        concentrations = list(
            worksheet.iloc[concentrationRow, 2:14]
        )

        concentrations[9] = "Blank"
        concentrations[10] = "URC"
        concentrations[11] = "URD"

        data = worksheet.iloc[
            startRow:endRow + 1,
            2:14
        ].copy()

        pairNames = list(
            worksheet.iloc[
                startRow:endRow + 1,
                0
            ]
        )

        data.columns = concentrations
        data.index = pairNames

        return data

    REGIONS = {
        "IMG": {
            "concentrationRow": 14,
            "startRow": 16,
            "endRow": 19
        },
        "AP": {
            "concentrationRow": 25,
            "startRow": 20,
            "endRow": 23
        },
        "Sample1": {
            "concentrationRow": 32,
            "startRow": 34,
            "endRow": 37
        },
        "Sample2": {
            "concentrationRow": 43,
            "startRow": 38,
            "endRow": 41
        }
    }

    assayData = {}

    for sampleName, region in REGIONS.items():

        assayData[sampleName] = extractRegion(
            worksheet,
            concentrationRow=region["concentrationRow"],
            startRow=region["startRow"],
            endRow=region["endRow"]
        )

    return assayData, workbookPath, worksheetName
