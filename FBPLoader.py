# coding: utf-8
import xlrd
import xlwt
import os

from constants import requiredColumnsSorted
from constants import headRowIdx, firstDataRowIdx

class FBPLoader(object):
	''' load the FBP meta data'''
	def __init__(self, wbPath, sheetName, headerIdx = headRowIdx, retainAllReqHdrs = False):
		self._fbp = xlrd.open_workbook(wbPath).sheet_by_name(sheetName)
		self._wbName = wbPath
		import logging
		self._logger = logging.getLogger("FBPLoader")
		self._logger.setLevel(logging.DEBUG)
		self._headRowIdx = headerIdx
		self.parseHeaderIndexes(retainAllReqHdrs)
		
	def parseHeaderIndexes(self, retainAllReqHdrs):
		''' parse header data and save meta data'''
		headline = self._fbp.row(self._headRowIdx)
		headvalues = [c.value for c in headline if len(unicode(c.value)) > 0]
		self._headData = headvalues
		#print headvalues
		
		indexes = {}
		from copy import deepcopy
		self._requiredColumnsSorted = deepcopy(requiredColumnsSorted)
		for headerName in self._requiredColumnsSorted:
			if headvalues.count(headerName) == 0:
				if not retainAllReqHdrs:
					self._requiredColumnsSorted.remove(headerName)
					self._logger.write("Specified column %s is not found in %s!\n"%(headerName, self._wbName))
			else:
				indexes[headerName] = headvalues.index(headerName)
		
		self._fbpIndexMap = indexes	

	def getAllHeaders(self):
		''' fetch all header info '''
		return self._headData
	
	def filterRowsByColPred(self, colNameList, pred):
		''' filter data by certain criteria pred(cellDataList)'''
		colIds = [self._fbpIndexMap[col] for col in colNameList]
		getValue = lambda rid: [self._fbp.cell(rid, colId).value for colId in colIds]
		return [rid for rid in range(firstDataRowIdx, self._fbp.nrows) \
			if pred(getValue(rid)) ]

	def getInterestedHeaderList(self):
		return self._headData
	
	def getIndexes(self):
		return self._fbpIndexMap
	
	def getBacklogSheetObj(self):
		return self._fbp

	def getFieldForRow(self, rowId, colHderName):
		if self._headData.count(colHderName) == 0:
			self._logger.error("required column %s not existed!", colHderName)
			self._logger.debug("existing headers:%s", ','.join([hdr for hdr in self._headData]))
			raise Exception("Invalid col header:%s"%colHderName)
		return self._fbp.cell(rowId, self._headData.index(colHderName)).value
