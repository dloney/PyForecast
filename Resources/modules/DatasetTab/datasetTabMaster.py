"""
Script Name:    datasetTabMaster.py

Description:    This script contains all the functionality associated with the 
                Datasets Tab. Operations such as finding and defining datasets
                as well as editing and deleting datasets are defined in this 
                script. The GUI behind the datasets tab is defined in the 
                resources.GUI.Tabs.DatasetsTab script.
"""

import pandas as pd
import os
from PyQt5 import QtCore, QtWidgets
from resources.modules.Miscellaneous import loggingAndErrors
from resources.modules.DatasetTab import gisFunctions
from resources.GUI.Dialogs import UserDefinedDatasetDialog, createCompositeDataset
from resources.modules.DatasetTab import hucClimDivCompleter
from fuzzywuzzy.fuzz import WRatio 
import multiprocessing as mp
import itertools
from time import sleep
import ast
import numpy as np

class datasetTab(object):
    """
    DATASETS TAB
    The Datasets Tab contains information about the selected datasets. It allows users to select and 
    configure datasets using the map or the search functionality.
    """

    def initializeDatasetTab(self):
        """
        Initialize the tab
        """

        self.connectEventsDatasetTab()
        self.loadDatasetCatalog()
        self.loadDatasetMap()

        return

    def connectEventsDatasetTab(self):
        """
        Connects all the signal/slot events for the dataset tab
        """

        # Buttons
        self.datasetTab.keywordSearchButton.clicked.connect(        lambda x: self.searchForDataset(self.datasetTab.keywordSearchBox.text()))
        self.datasetTab.boundingBoxButton.clicked.connect(          lambda x: self.beginDatasetAreaSearch("bounding"))
        self.datasetTab.hucSelectionButton.clicked.connect(         lambda x: self.beginDatasetAreaSearch("watershed"))
        self.datasetTab.boxHucSearchButton.clicked.connect(         lambda x: self.areaSearchForDatasets())
        self.datasetTab.prismButton.clicked.connect(                lambda x: self.addWatershedClimateDivisionDataset(self.prismCompleter.selectedDataset['DatasetExternalID'].iloc[0], 'PRISM'))
        self.datasetTab.nrccButton.clicked.connect(                 lambda x: self.addWatershedClimateDivisionDataset(self.nrccCompleter.selectedDataset['DatasetExternalID'].iloc[0], 'NRCC'))
        self.datasetTab.pdsiButton.clicked.connect(                 lambda x: self.addWatershedClimateDivisionDataset(self.climCompleter.selectedDataset['DatasetExternalID'].iloc[0], 'PDSI'))
        self.datasetTab.spiButton.clicked.connect(                  lambda x: self.addWatershedClimateDivisionDataset(self.climCompleter.selectedDataset['DatasetExternalID'].iloc[0], 'SPI'))
        self.datasetTab.climButton.clicked.connect(                 lambda x: self.addDataset(self.datasetTab.climInput.currentData().name))
        self.datasetTab.keywordSearchBox.returnPressed.connect(     lambda: self.searchForDataset(self.datasetTab.keywordSearchBox.text()))
        self.datasetTab.addiButton.clicked.connect(                 lambda x: self.openUserDefinedDatasetEditor())

        # Map Features
        self.datasetTab.webMapView.page.java_msg_signal.connect(    self.addDatasetsFromWebMap)
        
        # Listwidgets
        self.datasetTab.selectedDatasetsWidget.itemDoubleClicked.connect(               self.navigateMapToSelectedItem)
        self.datasetTab.searchResultsBox.itemDoubleClicked.connect(                     self.navigateMapToSelectedItem)
        self.datasetTab.boxHucResultsBox.itemDoubleClicked.connect(                     self.navigateMapToSelectedItem)
        self.datasetTab.searchResultsBox.buttonPressSignal.connect(                     self.addDataset)
        self.datasetTab.boxHucResultsBox.buttonPressSignal.connect(                     self.addDataset)
        self.datasetTab.selectedDatasetsWidget.buttonPressSignal.connect(               self.openUserDefinedDatasetEditor)
        self.datasetTab.selectedDatasetsWidget.Remove_DatasetAction.triggered.connect(  lambda x: self.removeDataset(self.datasetTab.selectedDatasetsWidget.currentItem().data(QtCore.Qt.UserRole).name))



        return

    

    def loadDatasetCatalog(self):
        """
        Reads the dataset catalogs located at /resources/GIS/ and loads them into 2 
        dataframes ('additionalDatasetsTable', 'searchableDatasetsTable').
        """

        # Read the dataset catalogs into pandas dataframes
        self.searchableDatasetsTable = pd.read_excel("resources/GIS/PointDatasets.xlsx", dtype={"DatasetExternalID": str, "DatasetHUC8":str}, index_col=0)
        self.searchableDatasetsTable.index.name = 'DatasetInternalID'
        self.additionalDatasetsTable = pd.read_excel('resources/GIS/AdditionalDatasets.xlsx', dtype={"DatasetExternalID": str,  "DatasetHUC8":str}, index_col=0)
        self.additionalDatasetsTable.index.name = 'DatasetInternalID'

        # Also, populate the climate indices
        for i, dataset in self.additionalDatasetsTable[self.additionalDatasetsTable['DatasetType'] == 'CLIMATE INDICE'].iterrows():
            self.datasetTab.climInput.insertItem(i, dataset['DatasetName'], dataset)
        
        
        # Create Completers for the watershed / climate division inputs / Climate Division
        self.prismCompleter = hucClimDivCompleter.hucClimDivCompleter()
        self.prismCompleter.setModelWithDataFrame(self.additionalDatasetsTable[(self.additionalDatasetsTable['DatasetAgency'] == 'PRISM') & (self.additionalDatasetsTable['DatasetParameterCode'] == 'avgt')])
        self.datasetTab.prismInput.setCompleter(self.prismCompleter)

        self.nrccCompleter = hucClimDivCompleter.hucClimDivCompleter()
        self.nrccCompleter.setModelWithDataFrame(self.additionalDatasetsTable[(self.additionalDatasetsTable['DatasetAgency'] == 'NRCC') & (self.additionalDatasetsTable['DatasetParameterCode'] == 'avgt')])
        self.datasetTab.nrccInput.setCompleter(self.nrccCompleter)

        self.climCompleter = hucClimDivCompleter.hucClimDivCompleter()
        self.climCompleter.setModelWithDataFrame(self.additionalDatasetsTable[(self.additionalDatasetsTable['DatasetType'] == 'PDSI')])
        self.datasetTab.pdsiInput.setCompleter(self.climCompleter)

        
        return

    def loadDatasetMap(self):
        """
        Loads the dataset catalog into the leaflet map
        """

        # Check if the file exists (or if the 'reset_map' flag is false)
        if 'map_data.geojson' in os.listdir('resources/temp') and self.userOptionsConfig['DATASETS TAB']['reset_map'] == 'False':
            with open('resources/temp/map_data.geojson', 'r') as readFile:
                geojson_ = readFile.read()

        else:
            # Create a geojson file of all the point datasets
            geojson_ = gisFunctions.dataframeToGeoJSON(self.searchableDatasetsTable)

            # Save the geojson file locally in the temp folder
            with open('resources/temp/map_data.geojson', 'w') as writeFile:
                writeFile.write(geojson_)

        # Load the geojson file into the web map
        self.datasetTab.webMapView.page.loadFinished.connect(lambda x: self.datasetTab.webMapView.page.runJavaScript("loadDatasetCatalog({0})".format(geojson_)))

        return


    def addDataset(self, datasetInternalID = None):
        """
        Adds the dataset defined by the datasetInternalID to the self.datasetTable table.
        This function also updates the dataset list in the GUI.

        Arguments:
            datasetInternalID -> The DatasetInternalID associated with the dataset to add. The ID's are 
                                 found in the dataset catalogs.
        """

        # Check to make sure that this dataset in not already in the datasetTable
        if datasetInternalID in list(self.datasetTable.index):

            # PRINT ERROR ABOUT THE DATASET ALREADY BEING 
            loggingAndErrors.showErrorMessage(self, "Dataset already selected")

            return
        
        # Find the dataset from the appropriate dataset catalog
        if datasetInternalID > 99999:        # This is a point dataset

            # Get the specific dataset
            dataset = self.searchableDatasetsTable.loc[datasetInternalID]
            
        else:                               # This is a HUC/CLIM/PDSI/OTHER dataset

            # Get the specific dataset
            dataset = self.additionalDatasetsTable.loc[datasetInternalID]
        
        # Append the dataset to the dataset table
        self.datasetTable = self.datasetTable.append(dataset, ignore_index = False)

        # Refresh the dataset list view
        self.datasetTab.selectedDatasetsWidget.setDatasetTable(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} DATASETS HAVE BEEN SELECTED:".format(len(self.datasetTable)))

        # Also refresh the dataset lists elsewhere in the software
        self.dataTab.datasetList.setDatasetTable(self.datasetTable)
        self.modelTab.datasetList.setDatasetTable(self.datasetTable)

        return
    
    def removeDataset(self, datasetInternalID = None):
        """
        Removes the dataset defined by the datasetInternalID from the self.datasetTable table.
        This function also updates the dataset list in the GUI.

        Arguments:
            datasetInternalID -> The DatasetInternalID associated with the dataset to add. The ID's are 
                                 found in the dataset catalogs.
        """

        # Provide a warning that this will delete all associated forecasts, data, etc associated with this id
        ret = loggingAndErrors.displayDialogYesNo("This action will remove any associated data using this dataset (e.g. forecasts, forecast equations, composite datasets). Continue?")
        if ret == False:
            return
        
        # Begin by removing the dataset from the datasetTable
        self.datasetTable.drop(datasetInternalID, inplace = True)

        # Next remove all data from the DataTable
        self.dataTable.drop(datasetInternalID, level='DatasetInternalID', inplace = True)

        # Update the multiIndex of the DataTable
        self.dataTable.set_index(self.dataTable.index.remove_unused_levels(), inplace = True)

        # Next, remove any datasets that depend on this dataset (i.e. composite datasets)
        for i, dataset in self.datasetTable.iterrows():
            if str(datasetInternalID) in str(dataset['DatasetCompositeEquation']):
                self.removeDataset(dataset.name)

        # Refresh the dataset list view
        self.datasetTab.selectedDatasetsWidget.setDatasetTable(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} DATASETS HAVE BEEN SELECTED:".format(len(self.datasetTable)))

        # Also refresh the dataset lists elsewhere in the software
        self.dataTab.datasetList.setDatasetTable(self.datasetTable)
        self.dataTab.spreadsheet.model().loadDataIntoModel(self.dataTable, self.datasetTable)
        self.modelTab.datasetList.setDatasetTable(self.datasetTable)
        self.dataTab.plot.clearPlots()

        return

    def openUserDefinedDatasetEditor(self, datasetID = None):
        """
        Opens the user defined dataset editor. Allows the user 
        to create custom datasets (import files, composite, custom loaders, etc).
        Initializes to the given ID, or it the ID is None, then initializes
        to a blank dataset
        """

        # Figure out if we're editing an existing dataset 
        if datasetID in list(self.datasetTable.index):
            
            # Get the dataset to be edited
            dataset = self.datasetTable.loc[datasetID]
        
        else:

            # Create a blank dataset to be edited
            if list(self.datasetTable.index) == []:
                newID = 900000
            else:
                newID = max(self.datasetTable.index) + 1 if max(self.datasetTable.index) >= 900000 else 900000
            dataset = pd.Series(
                data = ['OTHER','','','','','','','average','','',np.nan, np.nan, np.nan, '','','','',{}],
                index = [
                        'DatasetType',              # e.g. STREAMGAGE, or RESERVOIR
                        'DatasetExternalID',        # e.g. "GIBR" or "06025500"
                        'DatasetName',              # e.g. Gibson Reservoir
                        'DatasetAgency',            # e.g. USGS
                        'DatasetParameter',         # e.g. Temperature
                        "DatasetParameterCode",     # e.g. avgt
                        'DatasetUnits',             # e.g. CFS
                        'DatasetDefaultResampling', # e.g. average 
                        'DatasetDataloader',        # e.g. RCC_ACIS
                        'DatasetHUC8',              # e.g. 10030104
                        'DatasetLatitude',          # e.g. 44.352
                        'DatasetLongitude',         # e.g. -112.324
                        'DatasetElevation',         # e.g. 3133 (in ft)
                        'DatasetPORStart',          # e.g. 1/24/1993
                        'DatasetPOREnd',            # e.g. 1/22/2019\
                        'DatasetCompositeEquation', # e.g. C/100121,102331,504423/1.0,0.5,4.3/0,0,5
                        'DatasetImportFileName',    # e.g. 'C://Users//JoeDow//Dataset.CSV'
                        'DatasetAdditionalOptions'],
                name = newID
                
            )

        # Open the dialog with the dataset
        self.editorDialog = UserDefinedDatasetDialog.EditorDialog(self, dataset)

        # Connect the close events
        self.editorDialog.saveDatasetSignal.connect(self.saveUserDefinedDataset)
        
        return
    

    def saveUserDefinedDataset(self, dataset):
        """
        Connected to the saveDatasetSignal of the Editor Dialog. Updates the
        global DatasetTable with the updated or new datset
        """

        # Check if dataset is new
        if dataset.name in list(self.datasetTable.index):
            
            # Update the dataset table
            self.datasetTable.update(dataset)

        else:

            # Create a new row in the dataset table
            self.datasetTable = self.datasetTable.append(dataset, ignore_index = False)

        # NEED TO FIGURE OUT IF WE NEED TO UPDATE THE DATA OR DELETE ANY DATASETS ? FORECASTS ? ETC

        # Update the display
        self.datasetTab.selectedDatasetsWidget.setDatasetTable(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} DATASETS HAVE BEEN SELECTED:".format(len(self.datasetTable)))

        # Also refresh the dataset lists elsewhere in the software
        self.dataTab.datasetList.setDatasetTable(self.datasetTable)


    def addDatasetsFromWebMap(self, datasetAdditionMessage):
        """
        This function reads in console messages from the web map. Those messages
        are generated when a user selects the 'add dataset' buttons on the pop-ups.
        This function correctly routes the data from those messages
        """

        # Simplest case: user selected a point dataset
        if 'ID:' in datasetAdditionMessage:

            # Parse out the datasetID
            datasetID = int(datasetAdditionMessage.split(':')[1])

            # Add the dataset
            self.addDataset(datasetID)
        
        # User selected an area dataset
        elif 'HUC:' in datasetAdditionMessage or 'PDSI:' in datasetAdditionMessage:

            # Parse out the areaNumber
            areaNumber = datasetAdditionMessage.split(':')[1]

            # Parse out the datasetType
            datasetType = datasetAdditionMessage.split(':')[3]

            # Add the dataset
            self.addWatershedClimateDivisionDataset(areaNumber, datasetType)

        # Other javascript messages
        else:
            return

        return


    def addWatershedClimateDivisionDataset(self, areaNumber = None, datasetType = None):
        """
        Adds the watershed and datatype dataset to the datasetTable

        input:  areaNumber
                - The HUC8 of the watershed to add, or the 4 digit climate division code

                datasetType
                - one of ['PRISM', 'NRCC', 'PDSI', 'SPI']
        """

        # Retrieve watershed datasets
        if datasetType in ['PRISM', 'NRCC']:
            datasets = self.additionalDatasetsTable[(
                self.additionalDatasetsTable['DatasetAgency'] == datasetType) &
                (self.additionalDatasetsTable['DatasetExternalID'] == areaNumber
            )]

        # Retrieve Climate Division Datasets
        if datasetType in ['PDSI', 'SPI']:
            datasets = self.additionalDatasetsTable[(
                self.additionalDatasetsTable['DatasetType'] == datasetType) &
                (self.additionalDatasetsTable['DatasetExternalID'] == areaNumber
            )]

        # Add the datasets to the dataset Table
        for datasetID in list(datasets.index):
            self.addDataset(datasetID)

        return

    def beginDatasetAreaSearch(self, type_):
        """
        Begin the area search procedure by enabling BB or HUC selection in the map
        """

        # toggle the button enables
        self.datasetTab.boundingBoxButton.setEnabled(False)
        self.datasetTab.hucSelectionButton.setEnabled(False)
        self.datasetTab.boxHucSearchButton.setEnabled(True)
        
        # Tell the web map that we want to select HUCs or Areas
        if type_ == 'bounding':
            self.areaSearchType = 'bounding'
            self.datasetTab.webMapView.page.runJavaScript("enableBBSelect()")
        if type_ == 'watershed':
            self.areaSearchType = 'watershed'
            self.datasetTab.webMapView.page.runJavaScript("enableHUCSelect()")

        return

    def areaSearchForDatasets(self):
        """
        diable the area selection functionality and pass the selected hucs to the relevant search function
        """
        
        # Toggle the buttons
        self.datasetTab.boundingBoxButton.setEnabled(True)
        self.datasetTab.hucSelectionButton.setEnabled(True)
        self.datasetTab.boxHucSearchButton.setEnabled(False)
        
        # Retrieve the bounding boxes or the huc lists from the web map and route them to the area search function
        if self.areaSearchType == 'bounding':
            self.datasetTab.webMapView.page.runJavaScript("getBBCoords()", self.getDatasetFromBoundingBox)
        else:
            self.datasetTab.webMapView.page.runJavaScript("getSelectedHUCs()", self.getDatasetFromWatershedBoundaries)

        return

    def getDatasetFromBoundingBox(self, boundingBox = None):
        """
        searches the searchable datatsets table for stations located within the selected bounding box
        """
        n, w, s, e = [float(i) for i in str(boundingBox).split(':')[1].split('|')]
        results = self.searchableDatasetsTable[(self.searchableDatasetsTable['DatasetLongitude'] <= e) & (self.searchableDatasetsTable['DatasetLongitude'] >= w) & (self.searchableDatasetsTable['DatasetLatitude'] >= s) & (self.searchableDatasetsTable['DatasetLatitude'] <= n)] 
        self.datasetTab.boxHucResultsBox.setDatasetTable(results)

        return


    def getDatasetFromWatershedBoundaries(self, hucList = None):
        """
        This function searches the point dataset list and returns datasets that are inside of the 
        selected HUCS.
        """
        hucs = ast.literal_eval(str(hucList))
        results = self.searchableDatasetsTable[(self.searchableDatasetsTable['DatasetHUC8'].isin(hucs))]
        self.datasetTab.boxHucResultsBox.setDatasetTable(results)

        return

   

    def navigateMapToSelectedItem(self, item):
        """
        This function moves the map to the selected dataset (if it can be displayed on the map) that corresponds to the double-clicked item
        """
        lat = item.data(QtCore.Qt.UserRole)['DatasetLatitude']
        lng = item.data(QtCore.Qt.UserRole)['DatasetLongitude']
        self.datasetTab.webMapView.page.runJavaScript("moveToMarker({0},{1})".format(lat, lng))

        return

    def searchForDataset(self, searchTerm = None):
        """
        Searched the default dataset list and returns any potential matches

        input:  searchTerm
                - The keyword or keywords to search the default dataset list for.
                  example: 'Yellowstone River Billings'
        
        output: results
                - a dataframe of results which is a subset of the searchableDatasetsTable
        """

        # Begin by disabling the search button while we look
        self.datasetTab.keywordSearchButton.setEnabled(False)

        # Ensure that the search term is longer than 4 characters (the fuzzy search doesn't work well with short search terms)
        if len(searchTerm) < 4: 

            # ADD POPUP BOX TO TELL USER ABOUT THE ERROR
            loggingAndErrors.showErrorMessage("Search term is too broad, please enter a longer search term.")
            self.datasetTab.keywordSearchButton.setEnabled(True)
            return
        
        # Create a copy of the searchable dataset list
        searchTable = self.searchableDatasetsTable.copy()

        # Create a column in the searchTable containing all the keywords
        searchTable['searchColumn'] = searchTable[['DatasetName', 'DatasetType','DatasetAgency', 'DatasetExternalID']].apply(lambda x: ' '.join(x), axis=1)

        # Create a multiprocessing pool to perform the search
        pool = mp.Pool(mp.cpu_count() - 1)

        # Compute the scores (the fit score of the search term against the search column)
        searchTable['score'] = list(pool.starmap(WRatio, zip(searchTable['searchColumn'], itertools.repeat(searchTerm, len(searchTable)))))

        # Close the pool
        pool.close()
        pool.join()

        # Order the search results by score and load the results into the listWidget
        searchTable.sort_values(by=['score'], inplace=True, ascending=False)
        del searchTable['score'], searchTable['searchColumn']
        
        self.datasetTab.searchResultsBox.setDatasetTable(searchTable.iloc[0:30])

        self.datasetTab.keywordSearchButton.setEnabled(True)

        return