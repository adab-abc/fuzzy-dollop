# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 11:48:56 2026

@author: adabreo
"""

from parser import parseWorkbook
from analyzer import analyzeAssay
from reporter import generateExcelReport

assayData, workbookPath, worksheetName = parseWorkbook()
analysisData = analyzeAssay(assayData)

generateExcelReport(
    workbookPath,
    worksheetName,
    analysisData
)
