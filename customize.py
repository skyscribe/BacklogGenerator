# coding: utf-8

import xlwt
from copy import deepcopy
from constants import requiredColumnsSorted, level1ColumnsSorted

styles = {}
def getCellStyle(rowId, colId, rowData, headerData = requiredColumnsSorted):
	'''Customize the row by row data '''
	if len(styles.keys()) == 0:
		_initStyles()
	styleName = rowId == 0 and 'headerStyle' or _getColStyleName(rowData[colId], colId, headerData)
	return styles.has_key(styleName) and styles[styleName] or styles['defaultStyle']

def _initStyles():
	''' Initiate style objects'''
	global styles
	if len(styles.keys()) != 0:
		return

	borders = xlwt.Borders()
	borders.left = xlwt.Borders.THIN;
	borders.right = xlwt.Borders.THIN;		
	borders.top = xlwt.Borders.THIN;
	borders.bottom = xlwt.Borders.THIN;
	defaultStyle = xlwt.XFStyle()
	defaultStyle.borders = borders

	#Check settings from http://blog.sina.com.cn/s/blog_5357c0af01019gjo.html
	headerPattern = xlwt.Pattern()
	headerPattern.pattern = xlwt.Pattern.SOLID_PATTERN
	headerPattern.pattern_fore_colour = 5 # May be: 8 through 63. 0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = Yellow, 6 = Magenta, ...
	headerStyle = deepcopy(defaultStyle)
	headerStyle.pattern = headerPattern		

	doneStyle = deepcopy(headerStyle)
	doneStyle.pattern.pattern_fore_colour = 23 #dark grey
	inProgressStyle = deepcopy(doneStyle)
	inProgressStyle.pattern.pattern_fore_colour = 3 #green	
	plannedStyle = deepcopy(doneStyle)
	plannedStyle.pattern.pattern_fore_colour = 17 
	prePlannedStyle = deepcopy(doneStyle)
	prePlannedStyle.pattern.pattern_fore_colour = 5 #yellow
	dontPlanStyle = deepcopy(doneStyle)
	dontPlanStyle.pattern.pattern_fore_colour = 7 #cyan
	noPlanStyle = deepcopy(doneStyle)
	noPlanStyle.pattern.pattern_fore_colour = 2 #red
	notPlannedStyle = noPlanStyle	
	obsoleteStyle = deepcopy(doneStyle)
	obsoleteStyle.pattern.pattern_fore_colour = 22 # Light grey

	availableStyles =  ['defaultStyle', 'headerStyle', 'doneStyle', 'inProgressStyle', 'plannedStyle', 'notPlannedStyle',
			'prePlannedStyle', 'dontPlanStyle', 'noPlanStyle', 'obsoleteStyle']
	localDict = locals()
	styles = { styleName: localDict[styleName] for styleName in availableStyles if styleName in localDict.keys()}

def _getColStyleName(cellValue, colId, headerData):
	'''Mark up all columns that are used for certain status'''
	styleName = 'defaultStyle'
	if _isStatusColumn(headerData[colId]):
		#Possible literals: xx% => 0.xx, done, don't plan, no plan, obsolete, planned, pre-planned, not planned
		status = cellValue
		status = str(status).strip('?$%!').replace("'", "").replace('-', ' ')
		if status.replace('.', '').isdigit():
			styleName = "InProgress"
		else:
			styleName = ''.join([word.lower().capitalize() for word in status.split(' ')])
		if len(status) > 2:
			styleName = styleName[0].lower() + styleName[1:] + 'Style'
		else:
			styleName = 'defaultStyle'
		#print "Style selected as %s for value <%s>, column hdr:%s"%(styleName, cellValue, headerData[colId])
	return styleName

_isStatusColumn = lambda columnHdr: columnHdr.lower().find('status') >= 0

####################################################################################################
# width control
colWidths = {}
def getWidthByColumn(colId, tableData, headerData = requiredColumnsSorted):
	'''calculate the width to fit in all data for a given column'''
	if not colWidths.has_key(colId):
		colMaxLen = max([len(unicode(rowData[colId])) for rowData in tableData[1:]])
		hdrLen = len(headerData[colId])
		#print "@@@@@@ colId:%d, maxColLen:%d, hdrLen:%d"%(colId, colMaxLen, hdrLen)
		hdrLen = hdrLen > colMaxLen*1.2 and colMaxLen*1.2 or hdrLen
		hdrLen = max(_isStatusColumn(headerData[colId]) and 6 or hdrLen, hdrLen)
		colMaxLen = min(25, max(colMaxLen, hdrLen, 3)) * 250 # once character ~ 250
		colWidths[colId] = int(colMaxLen)
	return colWidths[colId]

level1ColumnIds = []
def getColOutlineLevel(colId, headerData = requiredColumnsSorted):
	''' calculate the outline level'''
	global level1ColumnIds
	if len(level1ColumnIds) == 0:
		level1ColumnIds = [headerData.index(hdrName) for hdrName in headerData \
							if level1ColumnsSorted.count(hdrName) == 1]
	if colId in level1ColumnIds:
		return 0
	else:
		return 1
