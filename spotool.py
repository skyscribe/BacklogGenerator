from rabp import initLogger
from FBPLoader import FBPLoader
import logging
from rabp import fbpFileAbsPath
from rabp import fbpSheetName
from rabp import raBacklogPath

class FBPChecker(object):
	def __init__(self):
		self._logger = logging.getLogger("FBPChecker")
		self._logger.setLevel(logging.DEBUG)
		self._fbp = FBPLoader(fbpFileAbsPath, fbpSheetName)
		self._rabp = FBPLoader(raBacklogPath, u'backlog', headerIdx = 0, retainAllReqHdrs = True)
		self._effInvalid = lambda eff: str(eff) == '' or (not str(eff).replace('.', '').isdigit()) or int(eff) <= 1
		self._wrappedBanner = lambda banner: '%s %s %s'%('='*30, banner, '='*30)

	def checkAll(self):
		self.checkTODO()
		self.checkConflicts()
		self.checkForCPRIHEffortsNotGiven()
		self.checkFTEffortsNotGiven()
		self.checkEEMismatch()

	def checkTODO(self):
		self._check(['Status_TDD CPRI H', 'Common FB plan', 'Clarification of Scope', 'TDD Release'],
			lambda cols: cols[0] == 'no plan' and (not cols[1].endswith('park')), banner = 'TODO')

	def checkConflicts(self):
		self._check(['Status_TDD CPRI H', 'i_TDD CPRI H'], lambda cols: cols[0] == 'obsolete' 
			and (cols[1] == 'x' or cols[1] == 'u'), banner = "StatusConflictCheckOnCPRIH")

	def checkForCPRIHEffortsNotGiven(self):
		self._check(['i_TDD CPRI H', 'RealRemaining effort_TDD CPRI H', 'COMMON DEV STATUS'], lambda cols: cols[0] == 'x'
			and self._effInvalid(cols[1]) and cols[2] != 'done' and cols[2] != 'obsolete',
			banner = "CPRIHEffortsNotGiven")

	def checkFTEffortsNotGiven(self):
		self._check(['i_FT', 'Feature Team', 'RealRemaining effort_FT', 'COMMON DEV STATUS'], lambda cols: cols[0] == 'x'
			and (cols[1] == 'HZ03' or cols[1] == 'HZ04')
			and self._effInvalid(cols[2]) and cols[3] != 'done' and cols[3] != 'obsolete',
			banner = "FTEffortsNotGiven")

	def checkEEMismatch(self):
		getSumOfEfforts = lambda cols: sum([int(col) for col in cols if col != ''])
		self._crossCheck(
				columnsForFilter = ['Feature Team', 'RealRemaining effort_FT', 'RealRemaining effort_TDD CPRI H', 'RealRemaining effort_OMRefa'],
				filterCriteria1 = lambda cols: (cols[0] == 'HZ03' or cols[0] == 'HZ04') and getSumOfEfforts(cols[1:]) > 0,
				columnsForRAFilter = ['Remaining EE'],
				getResultFBP = lambda cols: getSumOfEfforts(cols[1:]), 
				getResultRA = lambda cols: cols[0] != '' and int(cols[0]) or 0,
				checker = lambda x, y : x == y,
				banner = "Remaining EE and FBP EE summary mismatch"
				)

	def _check(self, columnsForFilter, filterCriteria, banner):
		#Generic checker
		self._logger.info(self._wrappedBanner("Tasks " + banner + " beg"))
		for row in self._fbp.filterRowsByColPred(columnsForFilter, filterCriteria):
			fid = self._fbp.getFieldForRow(row, 'Feature or Subfeature')
			self._logger.debug("Check this feature:%s, details=<%s>", fid, ','.join(
				['%s = %s' % (col, self._fbp.getFieldForRow(row, col)) for col in columnsForFilter]))
		self._logger.info(self._wrappedBanner("Tasks " + banner + " end"))

	def _crossCheck(self, columnsForFilter, filterCriteria1, columnsForRAFilter, getResultFBP, getResultRA, checker, banner):
		# cross checker
		self._logger.info(self._wrappedBanner("Cross checker " + banner + " beg"))
		for row in self._fbp.filterRowsByColPred(columnsForFilter, filterCriteria1):
			fid = self._fbp.getFieldForRow(row, 'Feature or Subfeature')
			rows = self._rabp.filterRowsByColPred(['Feature or Subfeature'], lambda cols: cols[0] == fid)
			if len(rows) == 0:
				self._logger.warning("This row checker is skipped, please check this feature:%s, details=<%s>", fid, ','.join(
						['%s = %s' % (col, self._fbp.getFieldForRow(row, col)) for col in columnsForFilter]))
				continue

			getColValues = lambda loader, record, colNames: [loader.getFieldForRow(record, colName) for colName in colNames]
			FBPValues = getColValues(self._fbp, row, columnsForFilter)
			RAValues = getColValues(self._rabp, rows[0], columnsForRAFilter)
			resultFBP = getResultFBP(FBPValues)
			resultRA = getResultRA(RAValues)
			if checker(resultFBP, resultRA):
				pass
			else:
				getKVStr = lambda klist, vlist: ", ".join(['%s=%s'%(k,v) for k,v in zip(klist, vlist)])
				self._logger.warning("Checker on feature:%s failed, FBP details:<%s>, RA details:<%s>, resultFBP:%s, resultRA:%s",
						fid, getKVStr(columnsForFilter, FBPValues), getKVStr(columnsForRAFilter, RAValues),
						resultFBP, resultRA)
		self._logger.info(self._wrappedBanner("Cross checker " + banner + " end"))


def checkAll():
	initLogger('fpbchecker.log')
	checker = FBPChecker()
	checker.checkAll()
