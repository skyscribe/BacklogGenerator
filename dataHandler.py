# coding: utf-8
from copy import deepcopy

class DataHandler(object):
	def __init__(self, srcData, srcHdr, dstHdr, logger):
		self._srcData = deepcopy(srcData)
		for row in [record for record in self._srcData if len(str(record[0])) == 0 ]:
			self._srcData.remove(row)

		self._srcHdr = deepcopy(srcHdr) #_requiredColumnsSorted
		self._hdr = deepcopy(srcHdr) #new list than reference
		self._dstHdr = deepcopy(dstHdr) #_requiredFBPColumnsSorted
		self._data = []
		self._logger = logger
		self._mergeHeader()

	def getHeader(self):
		return self._hdr

	def getData(self):
		return self._data

	def _mergeHeader(self):
		localHeaders = [hdr for hdr in self._srcHdr] #new list object
		extraHeaders = [hdr for hdr in self._dstHdr if hdr not in localHeaders]
		print "extra headers:",extraHeaders
		for hdr in extraHeaders:
			pre = [self._dstHdr[preId] for preId in range(self._dstHdr.index(hdr), 0, -1) \
					if self._dstHdr[preId] in localHeaders]
			insertAfterId = (len(pre) != 0) and localHeaders.index(pre[0]) + 1 or 0
			localHeaders.insert(insertAfterId, hdr)
			self._logger.write('Saving new header %s in posId:%d\n'%(hdr, insertAfterId))
		self._hdr = localHeaders
		if 'Hint' not in self._hdr: self._hdr.append('Hint')
		self._setIndexes()

	def _setIndexes(self):
		#Indexes
		self._fidIndex = self._hdr.index('Feature or Subfeature')
		self._fidIndexSrc = self._srcHdr.index('Feature or Subfeature')
		self._priorityIndex = self._hdr.index('Common RL Product Backlog Priority')
		self._priorityIndexSrc = self._srcHdr.index('Common RL Product Backlog Priority')
		self._hintIndex = self._hdr.index('Hint')
		self._srcFidIndexMap = {self._srcData[rowId][self._fidIndexSrc]: rowId for rowId in range(0, len(self._srcData))}
		#print self._srcFidIndexMap.keys()

	def collectAndMergeData(self, filteredRowIds, getCellValue, isFidInUpstream):
		'''collect data from FBP and merge with local data'''
		data = []
		rowId = 0
		data.append([unicode(hdr) for hdr in self._hdr]) #Header
		
		for fbpRowId in filteredRowIds:
			colValue = lambda x: x not in self._dstHdr and u'default' or getCellValue(fbpRowId, hdr)
			rowData = [colValue(hdr) for hdr in self._hdr ]
			data.append(rowData)
			rowId = rowId + 1

		if len(self._srcData) > 0:
			self._mergeData(data, isFidInUpstream)
		else:
			self._data = data
			self._logger.write("Filtered %d records\n"%rowId)

	def _mergeData(self, combinedData, isFidInUpstream):
		'''Merge local loaded data with combinedData (3-way merge), and fill in missing column as possible'''
		self._isNewCol = lambda colId: self._srcHdr.count(self._hdr[colId]) == 0
		self._getLocalColId = lambda colId: self._srcHdr.index(self._hdr[colId])
		self._data = [combinedData[0]] #Save static header

		mergeCandidates = [rowRecord for rowRecord in combinedData[1:] if self._srcFidIndexMap.has_key(rowRecord[self._fidIndex])]
		importList = [rowRecord for rowRecord in combinedData[1:] if rowRecord not in mergeCandidates]
		self._logger.write('We have %d records for merge, %d records for import\n'%(len(mergeCandidates), len(importList)))

		eraseList = []
		for rowRecord in mergeCandidates:
			fid = rowRecord[self._fidIndex]
			localRowId = self._srcFidIndexMap[fid]
			localRecord = self._srcData[localRowId]
			assert(localRecord[self._fidIndexSrc] == fid)
			#self._logger.write('comparing local:%s<%d> with fbp:%s\n'%(localRecord[self._fidIndex], localRowId, fid))
			self._mergeRecord(rowRecord, localRecord)
			#Remove local record accordingly
			#self._logger.write('Merged record with fid=%s\n'%fid)
			eraseList.append(localRecord)
			self._data.append(rowRecord)
		
		#Update status for imported ones	
		for rowRecord in importList:
			#self._logger.write('Updating new record with fid=%s\n'%rowRecord[self._fidIndex])
			rowRecord[self._hintIndex] = u'imported'
			self._data.append(rowRecord)

		self._logger.write('Number of local records:%d, will remove %d of them which are merged!\n'%(len(self._srcData), len(eraseList)))		
		#Erase merged data
		for record in eraseList:
			self._srcData.remove(record)		

		#Remove dangling
		eraseList = []
		for rowData in self._srcData:
			fid = rowData[self._fidIndex]
			if fid.startswith("LBT") or fid.startswith("lbt") or fid.startswith("LTE") or fid.startswith("lte"):
				if not isFidInUpstream(rowData[self._fidIndex]):
					#Should have been merged and erased, but left here - implies no impacts
					eraseList.append(rowData)
			else:
				#local feature, keep still
				self._logger.write("Will keep %s as local\n"%fid)
				pass
		self._logger.write('Number of local records:%d, will remove %d of them as dangling!\n'%(len(self._srcData), len(eraseList)))
		for record in eraseList:
			self._srcData.remove(record)		

		#Keep local
		for rowData in self._srcData:
			self._logger.write("Keep local record with fid=%s\n"%rowRecord[self._fidIndex])
			rowRecord = [(self._isNewCol(col) and u'unspecified' or rowData[self._getLocalColId(col)])
									for col in range(0, len(self._hdr))]
			rowRecord[self._hintIndex] = u'local'
			self._data.append(rowRecord)
		self._logger.write("Filtered %d records\n"%len(self._data))

	def _mergeRecord(self, rowRecord, localRecord):
		diffColIds = []
		for col in range(0, len(rowRecord)): 
			if self._isNewCol(col) or localRecord[self._getLocalColId(col)] != rowRecord[col]:
				#new column or same colmn with different value
				diffColIds.append(col)
		for col in diffColIds:
			if (rowRecord[col] == 'default') and (not self._isNewCol(col)): 
				#Filled in during parsing (populate data previously) - definitely local column
				#self._logger.write("Set col:%d as %s\n"%(col, self._getLocalColId(col)))
				rowRecord[col] = localRecord[self._getLocalColId(col)]
			else:
				if self._isNewCol(col):
					localValue = u''
				else: 
					localValue = localRecord[self._getLocalColId(col)]
				newValue = rowRecord[col]
				if newValue == u'default': newValue = ''
				if len(unicode(localValue)) > 0:
					if len(unicode(newValue)) > 0:
						rowRecord[col] = newValue #keep new value and overwrite local
					else:
						rowRecord[col] = localValue #New value is "", keep local
				else:
					#Keep new value
					rowRecord[col] = newValue
					pass
		if len(diffColIds) > 0:
			rowRecord[self._hintIndex] = unicode(','.join([str(id) for id in diffColIds]))
		else:
			rowRecord[self._hintIndex] = u'updated'
		return diffColIds

	def purgeDoneFeatures(self):
		'''Perge the done features if all its sub-features and the parent feature is done'''
		self._fidIndex = self._hdr.index('Feature or Subfeature')
		self._raIndex = self._hdr.index('Requirement Area')
		statusIndex = self._hdr.index("COMMON DEV STATUS")
		isFeatureInMyRA = lambda row: row[self._raIndex] == 'TDD-AifSiteS'
		rowCnt = len(self._data)

		#Filter through second-level features as parent
		# A feature will be removed if all the sub-features of its parent is done
		isFeatureDone = lambda status: status == 'done' or status == 'obsolete'
		secondLevelParents = [row for row in self._data if isFeatureDone(row[statusIndex])]
		parentFeatureList = list(set([row[self._fidIndex] for row in secondLevelParents if row[self._fidIndex].count('-') <= 1]))
		keepList = []
		for parent in parentFeatureList:
			unDones = [row for row in self._data if row[self._fidIndex].find(parent) == 0 \
						and (not isFeatureDone(row[statusIndex]))]
			unDonesInRA = [row for row in unDones if isFeatureInMyRA(row)]
			#Have unDone features, and (have raUnDones or parent lead by RA) 
			if len(unDones) > 0 and ((len(unDonesInRA) > 0) or isFeatureInMyRA(parent)):
				keepList.append(parent)
				self._logger.write('Parent feature %s will be kept since below features undone:%s\n'%(\
						parent, ','.join([row[self._fidIndex] for row in unDones])))

		for featureName in [featureName for featureName in parentFeatureList if featureName not in keepList]:
			#remove all sub-features
			for row in [row for row in self._data if row[self._fidIndex].find(featureName) == 0]:
				self._logger.write('Remove done/obsolete feature:%s since all feature group is done/obsolete!\n'%row[self._fidIndex]);
				self._data.remove(row)
		self._logger.write('Leftover feture number:%d, removed:%d\n'%(len(self._data) - 1, rowCnt - len(self._data)))

	def sortData(self):
		''' sort data by backlog priority'''
		dataContent = self._data[1:]
		def sortByPrioAndName(x, y):
			ret = cmp(int(x[self._priorityIndex]), int(y[self._priorityIndex]))
			if ret == 0:
				ret = cmp(x[self._fidIndex], y[self._fidIndex])
			return ret
		dataContent.sort(sortByPrioAndName)

		self._data = [self._data[0]]
		self._data.extend(dataContent)
		self._logger.write("data sorted by column:%s\n"%(self._data[0][self._priorityIndex]))