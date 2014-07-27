from rabp import initLogger
from FBPLoader import FBPLoader
import logging
from rabp import fbpFileAbsPath
from rabp import fbpSheetName

class FBPChecker(object):
	def __init__(self):
		self._logger = logging.getLogger("FBPChecker")
		self._logger.setLevel(logging.DEBUG)
		self._fbp = FBPLoader(fbpFileAbsPath, fbpSheetName)
		self._effInvalid = lambda eff: str(eff) == '' or (not str(eff).isdigit()) or int(eff) <= 1

	def checkAll(self):
		self.checkTODO()
		self.checkConflicts()
		self.checkForCPRIHEffortsNotGiven()
		self.checkFTEffortsNotGiven()

	def checkTODO(self):
		self._check(['Status_TDD CPRI H'], lambda cols: cols[0] == 'no plan', 'TODO')

	def checkConflicts(self):
		self._check(['Status_TDD CPRI H', 'i_TDD CPRI H'], lambda cols: cols[0] == 'obsolete' 
			and (cols[1] == 'x' or cols[1] == 'u'), banner = "StatusConflictCheckOnCPRIH")

	def checkForCPRIHEffortsNotGiven(self):
		self._check(['i_TDD CPRI H', 'RealRemaining effort_TDD CPRI H'], lambda cols: cols[0] == 'x'
			and self._effInvalid(cols[1]), banner = "CPRIHEffortsNotGiven")

	def checkFTEffortsNotGiven(self):
		self._check(['i_FT', 'Feature Team', 'RealRemaining effort_FT'], lambda cols: cols[0] == 'x'
			and (cols[1] == 'HZ03' or cols[1] == 'HZ04')
			and self._effInvalid(cols[2]), banner = "FTEffortsNotGiven")

	def _check(self, columnsForFilter, filterCriteria, banner):
		#Generic checker
		self._logger.info("=================Tasks %s beg=============", banner)
		for row in self._fbp.filterRowsByColPred(columnsForFilter, filterCriteria):
			fid = self._fbp.getFieldForRow(row, 'Feature or Subfeature')
			self._logger.debug("Check this feature:%s, details=<%s>", fid, ','.join(
				['%s = %s' % (col, self._fbp.getFieldForRow(row, col)) for col in columnsForFilter]))
		self._logger.info("=================Tasks %s end=============", banner)


def checkTODO():
	initLogger('fpbchecker.log')
	checker = FBPChecker()
	checker.checkAll()
