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

		self._isOurFT = lambda ftCol: ftCol.upper() == 'HZ03' or ftCol.upper() == 'HZ04'
		self._isStatusDone = lambda st: st == 'done' or st == 'obsolete'

	def checkAll(self):
		self._logger.info("@"*80 + "Checking started")
		self.checkTODO()
		self.checkConflicts()
		self.checkForCPRIHEffortsNotGiven()
		self.checkFTEffortsNotGiven()
		self.checkEEMismatch()
		self.checkFBTargetMismatch()
		self._logger.info("@"*80 + "Checking done" + "\n" * 3)

	def checkTODO(self):
		self._check(['Status_TDD CPRI H', 'Common FB plan', 'Clarification of Scope', 'TDD Release'],
			lambda cols: cols[0] == 'no plan' and (not cols[1].endswith('park')), banner = 'not planned')

	def checkConflicts(self):
		self._check(['Status_TDD CPRI H', 'i_TDD CPRI H'], lambda cols: cols[0] == 'obsolete' 
			and (cols[1] == 'x' or cols[1] == 'u'), banner = "StatusConflictCheckOnCPRIH")

	def checkForCPRIHEffortsNotGiven(self):
		self._check(['i_TDD CPRI H', 'Status_TDD CPRI H', 'RealRemaining effort_TDD CPRI H', 'COMMON DEV STATUS'], 
			filterCriteria = lambda cols: cols[0] == 'x' and (not self._isStatusDone(cols[1])) \
										and self._effInvalid(cols[2]) and (not self._isStatusDone(cols[3])),
			banner = "CPRIHEffortsNotGiven")

	def checkFTEffortsNotGiven(self):
		self._check(['i_FT', 'Feature Team', 'RealRemaining effort_FT', 'Status_FT', 'COMMON DEV STATUS'], 
			filterCriteria = lambda cols: cols[0] == 'x'
								and (self._isOurFT(cols[1]) and (not self._isStatusDone(cols[3])))
								and self._effInvalid(cols[2])  
								and (not self._isStatusDone(cols[-1])), 
			banner = "FTEffortsNotGiven")

	def _check(self, columnsForFilter, filterCriteria, banner):
		#Generic checker
		self._logger.info(self._wrappedBanner("Tasks " + banner + " beg"))
		for row in self._fbp.filterRowsByColPred(columnsForFilter, filterCriteria):
			fid = self._fbp.getFieldForRow(row, 'Feature or Subfeature')
			self._logger.debug("Checker[%s] on this feature:%s, details=<%s>", banner, fid, ','.join(
				['%s = %s' % (col, self._fbp.getFieldForRow(row, col)) for col in columnsForFilter]))
		self._logger.info(self._wrappedBanner("Tasks " + banner + " end"))

	def checkEEMismatch(self):
		getSumOfEfforts = lambda cols: sum([int(col) for col in cols if col != ''])
		self._crossCheck(
				columnsForFilter = ['Feature Team', 'RealRemaining effort_FT', 'RealRemaining effort_TDD CPRI H', 'RealRemaining effort_OMRefa'],
				filterCriteria1 = lambda cols: (self._isOurFT(cols[0])) and getSumOfEfforts(cols[1:]) > 0,
				columnsForRAFilter = ['Remaining EE'],
				getResultFBP = lambda cols: getSumOfEfforts(cols[1:]), 
				getResultRA = lambda cols: cols[0] != '' and int(cols[0]) or 0,
				checker = lambda x, y : x == y,
				banner = "Remaining EE and FBP EE summary mismatch"
				)

	def checkFBTargetMismatch(self):
		hasFBPlan = lambda col: col.lower().startswith('fb')
		planToNumber = lambda plan: int(plan[len('fb'):].replace(".", ""))
		def fbNoLaterThan(x, y):
			if (not hasFBPlan(y)): return True #x always not late
			else:
				if hasFBPlan(x): return planToNumber(x) <= planToNumber(y)
				else: return False
		getEarliestFB = lambda fbList: reduce(lambda x, y: fbNoLaterThan(x, y) and x or y, fbList, '')
		getLatestFB = lambda fbList: reduce(lambda x, y: fbNoLaterThan(x, y) and y or x, fbList, '')

		self._crossCheck(
				columnsForFilter = ['Common FB plan', 'Feature Team', 'FB_FT', 'FB_TDD CPRI H', 'FB_BTSOM', 'OMRefa_Site', 'COMMON DEV STATUS'],
				filterCriteria1 = lambda cols: \
						(not cols[0].endswith('park'))  # parks - don't plan
						and (str(cols[-1]).lower() != 'done') # don't check done features 
						and (
								(self._isOurFT(cols[1]) and hasFBPlan(cols[2])) 	 #FT planned 
								or hasFBPlan(cols[3])                           	 #TDDCPRIH planned
								or (hasFBPlan(cols[4]) and cols[5].lower() == 'hzu') #OMHz planned
							),
				columnsForRAFilter = ['FB Target'],
				getResultFBP = lambda cols: filter(lambda fb: fb.lower().startswith('fb'), cols[2:-2]), #All sensible FBs
				getResultRA = lambda cols: cols[0],
				checker = lambda x, y: fbNoLaterThan(y, getLatestFB(x)), # y <= latestestFB
				banner = "FB Target not compliant with FBP SC/FT planning"
			)

	def _crossCheck(self, columnsForFilter, filterCriteria1, columnsForRAFilter, getResultFBP, getResultRA, checker, banner):
		# cross checker
		self._logger.info(self._wrappedBanner("Cross checker " + banner + " beg"))
		for row in self._fbp.filterRowsByColPred(columnsForFilter, filterCriteria1):
			fid = self._fbp.getFieldForRow(row, 'Feature or Subfeature')
			rows = self._rabp.filterRowsByColPred(['Feature or Subfeature'], lambda cols: cols[0] == fid)
			if len(rows) == 0:
				#self._logger.warning("This row checker is skipped, please check this feature:%s, details=<%s>", fid, ','.join(
				#		['%s = %s' % (col, self._fbp.getFieldForRow(row, col)) for col in columnsForFilter]))
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
				self._logger.warning("Checker[%s] on feature:%s failed, FBP details:<%s>, RA details:<%s>, resultFBP:%s, resultRA:%s",
						banner, fid, getKVStr(columnsForFilter, FBPValues), getKVStr(columnsForRAFilter, RAValues),
						resultFBP, resultRA)
		self._logger.info(self._wrappedBanner("Cross checker " + banner + " end"))


def checkAll():
	initLogger('fpbchecker.log')
	checker = FBPChecker()
	checker.checkAll()
