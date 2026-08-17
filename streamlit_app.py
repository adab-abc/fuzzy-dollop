import streamlit as st
import tempfile
import os

from parser import parseWorkbook
from analyzer import analyzeAssay
from reporter import generateExcelReport

st.set_page_config(
    page_title="Assay Processor",
    layout="wide"
)

st.title("Automated Assay Processing")

uploadedFile = st.file_uploader(
    "Upload Assay Workbook",
    type=["xlsx", "xlsm"]
)

if uploadedFile is not None:

    st.success("Workbook uploaded")

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(uploadedFile.name)[1]
    ) as tempFile:

        tempFile.write(uploadedFile.getvalue())

        workbookPath = tempFile.name

    try:

        assayData, workbookPath, worksheetName = parseWorkbook(
            workbookPath
        )

        st.write("Analyzing assay...")

        analysisData = analyzeAssay(
            assayData
        )

        generateExcelReport(
            workbookPath,
            worksheetName,
            analysisData
        )

        st.success("Analysis complete")

        with open(workbookPath, "rb") as file:

            st.download_button(
                label="Download Report Workbook",
                data=file,
                file_name=f"{worksheetName}_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as error:

        st.error(str(error))
