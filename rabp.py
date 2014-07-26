# coding: utf-8
import xlrd
import xlwt
import os
import logging

from customize import getCellStyle, getWidthByColumn, getColOutlineLevel
from constants import requiredColumnsSorted
from constants import headRowIdx, firstDataRowIdx, fbpSheetName, pathSep
from dataHandler import DataHandler
from FBPLoader import FBPLoader

#File names and sheet name
inputFileName = "LTE eNB Feature Build Plan.xlsm"
raBacklogFileName = "OM RA Backlog.xls"
workingFolder = os.getcwd()
fbpFileAbsPath = workingFolder + pathSep + inputFileName
raBacklogPath = workingFolder + pathSep + raBacklogFileName
	
class RABacklogGenerator(object):
	def __init__(self, fbpLoader, raBacklogPath, handler):
		self._fbp = fbpLoader
		self._fbpSheet = self._fbp.getBacklogSheetObj()
		self._requiredFBPColumnsSorted = self._fbp._requiredColumnsSorted
		self._requiredColumnsSorted = [v for v in self._requiredFBPColumnsSorted]
		self._fbpIndexMap = fbpLoader.getIndexes()
		self._raDataIn = []

		import sys
		self._logger = logging.getLogger(__name__)
		self._logger.setLevel(logging.DEBUG)

		self._raSheetName = u'backlog'
		self._raBacklogPath = raBacklogPath
		self.loadRABacklog()

		self._dataHandler = DataHandler(self._raDataIn, srcHdr = self._requiredColumnsSorted, \
			dstHdr = self._requiredFBPColumnsSorted, handler = handler)

	def loadRABacklog(self):
		try:
			self._raSheetIn = FBPLoader(self._raBacklogPath, self._raSheetName, headerIdx = 0, retainAllReqHdrs = True)
			self.loadRAData()
		except Exception, e:
			self._logger.warning("Available input sheet not valid, will be cleared:%s\n"%e.message) 
			self._raSheetIn = []

		#Result sheet
		book = xlwt.Workbook(raBacklogPath, style_compression = 2)
		sheet = book.add_sheet(self._raSheetName)
		self._raSheet = sheet

	def loadRAData(self):
		'''Load RA data by existing order, the header row is also saved here'''
		raSheet = self._raSheetIn.getBacklogSheetObj()
		self._raDataIn = [raSheet.row_values(rowId) for rowId in range(1, raSheet.nrows)]
		self._requiredColumnsSorted = self._raSheetIn.getAllHeaders()

	def generate(self):
		''' Generate OM RA backlog per filtering/merge/purge/sort '''
		columnsForRAChecking = ['Requirement Area', 'i_TDD CPRI H', 'Site_BTSOM', 'OM LTE_Site', 'OMRefa_Site']
		filterCriteria = lambda cols : (cols[0] == "TDD-AifSiteS") or (cols[1] == 'x') or (cols[1] == 'u') \
				or (cols[2] == 'Hzu') or (cols[3] == 'Hzu')
		rowIds = self._fbp.filterRowsByColPred(columnsForRAChecking, filterCriteria)
		self._logger.info("Totally %d records filtered from upstream FBP file", len(rowIds))

		getCellValue = lambda rowId, rowHdr: self._fbpSheet.cell(rowId, self._fbpIndexMap[rowHdr]).value

		from copy import copy
		columnsForFeatureCheckings = copy(columnsForRAChecking)
		columnsForFeatureCheckings.append('Feature or Subfeature')
		isFidValidInFBP = lambda fid: len(self._fbp.filterRowsByColPred(columnsForFeatureCheckings,
				lambda cols: filterCriteria(cols[:-1]) and cols[-1] == fid )) > 0
		
		self._dataHandler.collectAndMergeData(rowIds, getCellValue, isFidValidInFBP)

		self._dataHandler.purgeDoneFeatures()
		self._dataHandler.sortData()
		self._raData = self._dataHandler.getData()
		self.formatAndSaveData()
		
	def formatAndSaveData(self):
		''' Write data into new workbook '''
		sheet = self._raSheet
		book = self._raSheet.get_parent()
		header = self._raData[0]
		#NOTE: row styles will be overwritten when write is called!
		[sheet.write(rowId, colId, rowData[colId], getCellStyle(rowId, colId, rowData, header)) \
			for rowId, rowData in zip(range(0, len(self._raData)), self._raData)\
			for colId in range(0, len(rowData))]
		#Format width
		[sheet.col(colId).set_width(getWidthByColumn(colId, self._raData, header)) \
			for colId in range(0, len(header))]
		#Set outline
		for colId in range(0, len(header)):
			sheet.col(colId).level = getColOutlineLevel(colId, header)
		#Set freeze
		sheet.panes_frozen = True
		sheet.horz_split_pos = 1  #Always show header
		sheet.vert_split_pos = header.index('TDD Release')

		book.save(self._raBacklogPath)
	
def test1(fbp):
	#fbp = FBPLoader(fbpFileAbsPath, fbpSheetName)
	RABacklogGenerator(fbp, raBacklogPath).generate()

def generate():
	logging.getLogger().info("\n~~~~~~~~~~~~Start~~~~~~~~~~~\n")
	handler = initLogger()
	fbp = FBPLoader(fbpFileAbsPath, fbpSheetName)
	logging.getLogger().info("~~~~~~~~~~~~FBP Loaded now~~~~~~~~~~~")
	RABacklogGenerator(fbp, raBacklogPath, handler).generate()
	logging.getLogger().info("\n~~~~~~~~~~~~End~~~~~~~~~~~\n")

def initLogger():
	from logging.handlers import RotatingFileHandler
	handler = RotatingFileHandler(filename = "rabp.log", maxBytes = 2*1024*1024, backupCount=10)
	fmt = logging.Formatter(fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	handler.setFormatter(fmt)
	handler.setLevel(logging.DEBUG)
	logging.getLogger().addHandler(handler)
	return handler	

def testLogger():
	handler = initLogger()
	logger = logging.getLogger("test")
	logger.setLevel(logging.DEBUG)
	logger.info("test log")

	logging.getLogger("test.a").debug("debug info")