# -*- coding: utf-8 -*-
"""
Created on Wed Aug  5 14:50:49 2026

@author: adabreo
"""
import pandas as pd 
import numpy as np

from scipy.optimize import curve_fit
from scipy.optimize import root_scalar

def convertToPgMl(dataframe):
    convertedData = dataframe.copy()
    convertedData = convertedData * 1000
    return convertedData

def analyzeAssay(assayData):

    analysisData = {}

    for sampleName, dataframe in assayData.items():

        curveData, controlData = splitControls(dataframe)

        upperMask = determineUpperCutoffPoints(curveData)

        validCurveData = curveData.where(upperMask)

        blankValues = calculateBlankValues(controlData)

        blankSubtracted = subtractBlanks(
            validCurveData,
            blankValues
        )

        lowerCutoffs = calculateLowerCutoffs(blankValues)

        lowerMask = determineLowerCutoffPoints(
            blankSubtracted,
            lowerCutoffs
        )

        curveMask = upperMask & lowerMask

        curveFitData = createCurveFitData(
            blankSubtracted,
            upperMask
        )

        #
        # PRISM MODE
        #
        # Interpolate anything that is not overflow/saturated.
        # Do NOT apply lower cutoff masking before interpolation.
        #
        interpolationData = createInterpolationData(
            blankSubtracted,
            upperMask
        )

        if sampleName == "IMG":

            preparedCurves = prepareCurveData(curveFitData)

            fourPLFits = fitAllFourPL(preparedCurves)

            fivePLFits = fitAllFivePL(preparedCurves)

            modelComparison = compareModels(
                fourPLFits,
                fivePLFits
            )

        else:

            preparedCurves = None
            fourPLFits = None
            fivePLFits = None
            modelComparison = None

        if sampleName != "IMG":

            interpolatedData = interpolateSampleData(
                interpolationData,
                analysisData["IMG"]["fourPLFits"]
            )

            correctedData = correctForDilution(
                interpolatedData
            )

            linearityMatrices = createLinearityMatrices(
                correctedData
            )

        else:

            interpolatedData = None
            correctedData = None
            linearityMatrices = None

        analysisData[sampleName] = {
            "curveData": curveData,
            "controls": controlData,
            "blankValues": blankValues,
            "blankSubtracted": blankSubtracted,
            "lowerCutoffs": lowerCutoffs,
            "upperMask": upperMask,
            "lowerMask": lowerMask,
            "curveMask": curveMask,
            "curveFitData": curveFitData,
            "interpolationData": interpolationData,
            "preparedCurves": preparedCurves,
            "fourPLFits": fourPLFits,
            "fivePLFits": fivePLFits,
            "modelComparison": modelComparison,
            "interpolatedData": interpolatedData,
            "correctedData": correctedData,
            "linearityMatrices": linearityMatrices
        }

    return analysisData
            
def splitControls(dataframe):
    curveData = dataframe.iloc[:, 0:9]
    controls = dataframe[["Blank", "URC", "URD"]].copy()
    return curveData, controls

def findDuplicatePairs(dataframe):
    duplicatePairs = dataframe.index[dataframe.index.duplicated()]
    return list(duplicatePairs)

def calculateBlankValues(controls):
    blankValues = controls.groupby(controls.index)["Blank"].transform("mean")
    return blankValues

def subtractBlanks(curveData, blankValues):
    blankSubtracted = curveData.subtract(blankValues, axis=0)
    return blankSubtracted

def calculateLowerCutoffs(blanksValues):
    lowerCutoffs = blanksValues*1.3
    return lowerCutoffs

def determineUpperCutoffPoints(curveData):
    upperMask = pd.DataFrame(
        True,
        index=curveData.index,
        columns=curveData.columns
    )
    for row in curveData.index:
        for col in curveData.columns:
            value = curveData.loc[row, col]
            if str(value).strip().lower() == "overflow":
                upperMask.loc[row, col] = False
            elif pd.notna(value):
                if float(value) == 3.5:
                    upperMask.loc[row, col] = False
    return upperMask

def determineLowerCutoffPoints(blankSubtracted, lowerCutoffs):
    lowerMask = blankSubtracted.ge(lowerCutoffs, axis=0)
    return lowerMask

def createCurveFitData(blankSubtracted, upperMask):
    curveFitData = blankSubtracted.where(upperMask)
    return curveFitData

def prepareCurveData(curveFitData):

    preparedCurves = {}

    for pairName in curveFitData.index:

        xValues = []
        yValues = []

        for concentration in curveFitData.columns:

            yValue = curveFitData.loc[pairName, concentration]

            if pd.notna(yValue):

                concentrationValue = float(
                    str(concentration)
                    .replace(" ng/ml", "")
                    .replace(" mg/ml", "")
                )

                xValues.append(concentrationValue)

                yValues.append(yValue)

        preparedCurves[pairName] = {
            "x": np.array(xValues),
            "y": np.array(yValues)
        }

    return preparedCurves

def fourPL(x, A, B, C, D):
    return D + ((A - D) / (1 + (x / C) ** B))

def fitFourPL(xValues, yValues):

    initialGuess = [
        max(yValues),
        1.0,
        np.median(xValues),
        min(yValues)
    ]

    lowerBounds = [
        0,
        -10,
        0.0001,
        -1
    ]

    upperBounds = [
        10,
        10,
        100,
        10
    ]

    parameters, covariance = curve_fit(
        fourPL,
        xValues,
        yValues,
        p0=initialGuess,
        bounds=(lowerBounds, upperBounds),
        maxfev=10000
    )

    return parameters

def calculateRSquared(observedY, predictedY):
    observedY = np.array(observedY)
    residuals = observedY - predictedY
    ssResidual = np.sum(residuals ** 2)
    ssTotal = np.sum((observedY - np.mean(observedY)) ** 2)
    rSquared = 1 - (ssResidual / ssTotal)
    return rSquared

def predictFourPL(xValues, parameters):

    A, B, C, D = parameters

    return fourPL(
        np.array(xValues),
        A,
        B,
        C,
        D
    )

def fitAllFourPL(preparedCurves):

    fourPLFits = {}

    for pairName, curveData in preparedCurves.items():

        xValues = curveData["x"]
        yValues = curveData["y"]

        parameters = fitFourPL(
            xValues,
            yValues
        )

        predictedY = predictFourPL(
            xValues,
            parameters
        )

        rSquared = calculateRSquared(
            yValues,
            predictedY
        )

        fourPLFits[pairName] = {
            "xValues": xValues,
            "yValues": yValues,
            "parameters": parameters,
            "predictedY": predictedY,
            "rSquared": rSquared
        }

    return fourPLFits

def fivePL(x, A, B, C, D, G):
    return D + ((A - D) / ((1 + (x / C) ** B) ** G))

def fitFivePL(xValues, yValues):

    initialGuess = [
        max(yValues),
        1.0,
        np.median(xValues),
        min(yValues),
        1.0
    ]

    lowerBounds = [
        0,
        -10,
        0.0001,
        -1,
        0.01
    ]

    upperBounds = [
        10,
        10,
        100,
        10,
        10
    ]

    parameters, covariance = curve_fit(
        fivePL,
        xValues,
        yValues,
        p0=initialGuess,
        bounds=(lowerBounds, upperBounds),
        maxfev=10000
    )

    return parameters

def predictFivePL(xValues, parameters):
    A, B, C, D, G = parameters
    predictedY = fivePL(np.array(xValues),A,B,C,D,G)
    return predictedY

def fitAllFivePL(preparedCurves):
    fivePLFits = {}
    for pairName, curveData in preparedCurves.items():
        xValues = curveData["x"]
        yValues = curveData["y"]
        parameters = fitFivePL(xValues, yValues)
        predictedY = predictFivePL(xValues, parameters)
        rSquared = calculateRSquared(yValues, predictedY)
        fivePLFits[pairName] = {
            "xValues": xValues,
            "yValues": yValues,
            "parameters": parameters,
            "predictedY": predictedY,
            "rSquared": rSquared
        }
    return fivePLFits

def compareModels(fourPLFits, fivePLFits):
    modelComparison = {}
    for pairName in fourPLFits:
        fourPLRSquared = fourPLFits[pairName]["rSquared"]
        fivePLRSquared = fivePLFits[pairName]["rSquared"]
        modelComparison[pairName] = {
            "fourPLRSquared": fourPLRSquared,
            "fivePLRSquared": fivePLRSquared,
            "deltaRSquared": fivePLRSquared - fourPLRSquared
        }
    return modelComparison
###Standard Interpolation - Withing Std Curve Range Only
'''
def interpolateFourPL(yValue, parameters):
    A, B, C, D = parameters
    try:
        denominator = yValue - D
        if denominator == 0:
            return np.nan
        ratio = ((A - D) / denominator) - 1
        if ratio <= 0:
            return np.nan
        xValue = C * (ratio ** (1 / B))
        return xValue
    except Exception:
        return np.nan
'''

def interpolate4PL(yValue, parameters):

    if pd.isna(yValue):
        return np.nan

    A, B, C, D = parameters

    upperAsymptote = max(A, D)
    lowerAsymptote = min(A, D)

    if yValue >= upperAsymptote:
        return np.nan

    if yValue <= lowerAsymptote:
        return np.nan

    try:

        ratio = ((A - D) / (yValue - D)) - 1

        if ratio <= 0:
            return np.nan

        concentrationNgMl = C * (ratio ** (1 / B))

        concentrationPgMl = concentrationNgMl * 1000

        return concentrationPgMl

    except Exception:

        return np.nan
    
def createInterpolationData(blankSubtracted, curveMask):
    interpolationData = blankSubtracted.where(curveMask)
    return interpolationData

def interpolateSampleData(interpolationData, fourPLFits):

    interpolatedData = interpolationData.copy()

    for pairName in interpolatedData.index:

        if pairName not in fourPLFits:
            continue

        parameters = fourPLFits[pairName]["parameters"]

        for column in interpolatedData.columns:

            yValue = interpolatedData.loc[pairName, column]

            if pd.notna(yValue):

                interpolatedData.loc[pairName, column] = interpolate4PL(
                    yValue,
                    parameters
                )

    return interpolatedData

def correctForDilution(interpolatedData):
    dilutionFactors = [1, 2, 4, 8, 16, 32, 64]
    correctedData = interpolatedData.copy()
    for row in correctedData.index:
        for columnIndex, column in enumerate(correctedData.columns):
            if columnIndex >= len(dilutionFactors):
                break
            value = correctedData.loc[row, column]
            if pd.notna(value):
                correctedData.loc[row, column] = (
                    value * dilutionFactors[columnIndex]
                )
    return correctedData

def calculateRelativePercent(correctedData):
    relativeData = correctedData.copy()
    for pairName in correctedData.index:
        firstValid = correctedData.loc[pairName].dropna()
        if len(firstValid) == 0:
            continue
        baseline = firstValid.iloc[0]
        relativeData.loc[pairName] = (
            correctedData.loc[pairName] / baseline
        ) * 100
    return relativeData

def calculateLinearityMatrix(correctedValues):

    validValues = correctedValues.dropna()

    matrix = pd.DataFrame(
        np.nan,
        index=validValues.index,
        columns=validValues.index
    )

    for dilution in validValues.index:

        matrix.loc[dilution, dilution] = 100

    for rowIndex, rowDilution in enumerate(validValues.index):

        for colIndex, colDilution in enumerate(validValues.index):

            if rowIndex <= colIndex:

                continue

            relativePercent = (
                validValues[rowDilution]
                / validValues[colDilution]
            ) * 100

            matrix.loc[rowDilution, colDilution] = relativePercent

    dilutionFactors = [
        2 ** i
        for i in range(len(matrix.index))
    ]

    matrix.index = dilutionFactors

    matrix.columns = dilutionFactors

    return matrix

def createLinearityMatrices(correctedData):
    linearityMatrices = {}
    for pairName in correctedData.index:
        matrix = calculateLinearityMatrix(correctedData.loc[pairName])
        linearityMatrices[pairName] = matrix
    return linearityMatrices

