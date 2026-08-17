# -*- coding: utf-8 -*-

import os
import tempfile
import streamlit as st
import pandas as pd

from parser import parseWorkbook
from analyzer import analyzeAssay
from reporter import generateExcelReport

st.set_page_config(
    page_title="Automated Assay Processor",
    layout="wide"
)

st.title("Automated Assay Processing Tool")

st.write(
    """
    Upload an assay workbook,
    select a worksheet,
    run the analysis,
    and download the completed report.
    """
)

uploadedFile = st.file_uploader(
    "Upload Excel Workbook",
    type=["xlsx", "xlsm"]
)

if uploadedFile is not None:

    suffix = os.path.splitext(uploadedFile.name)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tempFile:

        tempFile.write(uploadedFile.getvalue())

        workbookPath = tempFile.name

    excelBook = pd.ExcelFile(workbookPath)

    worksheetName = st.selectbox(
        "Select Worksheet",
        excelBook.sheet_names
    )

    if st.button("Process Workbook"):

        try:

            with st.spinner("Parsing workbook..."):

                assayData, workbookPath, worksheetName = parseWorkbook(
                    workbookPath,
                    worksheetName
                )

            with st.spinner("Analyzing assay data..."):

                analysisData = analyzeAssay(
                    assayData
                )

            with st.spinner("Generating report..."):

                generateExcelReport(
                    workbookPath,
                    worksheetName,
                    analysisData
                )

            reportPath = workbookPath

            st.success(
                "Analysis complete."
            )

            with open(reportPath, "rb") as reportFile:

                st.download_button(
                    label="Download Report Workbook",
                    data=reportFile,
                    file_name=f"{worksheetName}_Report{suffix}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        except Exception as error:

            st.error(
                f"Analysis failed:\n{str(error)}"
            )
