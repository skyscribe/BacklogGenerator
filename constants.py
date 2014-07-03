# coding: utf-8

#File names and sheet name
inputFileName = "LTE eNB Feature Build Plan.xlsm"
outputFileName = "OM RA Backlog.xls"
workingFolder = "D:\\FOT\\RABP\\"

fbpSheetName = "FBPlan"
pathSep = "\\"

#Stable table structure
headRowIdx = 2
firstDataRowIdx = 7

requiredColumnsSorted = [
	"Feature or Subfeature",
	"Name",
	"Clarification of Scope",
	"Common RL Product Backlog Priority",
	"Common FB plan",
	"COMMON DEV STATUS",
	"TDD Release",
	"Requirement Area",

	"EFS status",
	"Feature Owner",
	"i_PDDB",
	"Status_PDDB",
	"i_RISE Counter",
	"Status_RISE Counter",
	"i_RISE Alarm",
	"Status_BPF",
	"i_BPF",
	"SDT of Feature Owner",
	"Status_CFAM",

	"FOT",
	"Agreed last SW delivery",
	"Agreed EI execution  start",
	"Feature Team",
	"FB_FT",
	"Status_FT",

	#OM status
	"FB_BTSOM",
	"Status_BTSOM",
	"Site_BTSOM",
	"Initial effort_BTSOM",
	"i_BTSOM",
	"eTM_BTSOM",
	"OM LTE_Site",
	"Initial Effort_OM LTE",
	"RealRemaining effort_OM LTE",

	#TDD CPRI Handler
	"FB_TDD CPRI H",
	"Status_TDD CPRI H",
	"RealRemaining effort_TDD CPRI H",
	"i_TDD CPRI H",

	#Other reference columns
	"FB_TDD U-Plane",
	"FB_MAC PS",	
	"Status_MAC PS",
	"FB_C-plane",
	"Status_C-Plane",
	"FB_BM",
	"Status_BM",
	"FB_BTSSM",
	"Status_BTSSM",
	"FB_Platform",
	"Status_Platform",
	"FB_FTM",
	"Status_FTM",
	"FB_RF",
	"Status_RF",
	"FB_SCM",
	"Status_SCM",
]

level1ColumnsSorted = [
	"Feature or Subfeature",
	"Name",
	"Common FB plan",
	#"COMMON DEV STATUS",
	"TDD Release",
	"Requirement Area",
	"EFS status",
	"FOT",
	"FB_BTSOM",
	"FB_TDD CPRI H",
	"FB_TDD U-Plane",
	"FPO", #customized header
]
