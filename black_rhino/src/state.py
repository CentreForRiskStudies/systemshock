#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
black_rhino is a multi-agent simulator for financial network analysis
Copyright (C) 2012 Co-Pierre Georg (co-pierre.georg@keble.ox.ac.uk)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


#------------------------------------------------------------------------------
#  class State
#------------------------------------------------------------------------------
class State(object):
	#
	# VARIABLES
	#
	rb = 0.0 # interbank interest rate
	rd = 0.0 # interest rate on deposits
	r = 0.0 # minimum required deposit rate
	sifiSurchargeFactor = 1.0 # the surcharge on banking capital that SIFIs have to hold
	collateralQuality = 0.0 # the fraction of a bank's portfolio that the central bank accepts as collateral
	successProbabilityFirms = 0.0 # probability of successful credit
	positiveReturnFirms = 0.0 # return for a successful credit
	scaleFactorHouseholds = 0.0 # scaling factor for deposit fluctuations
	dividendLevel = 0.0 # dividend level as paid out by banks
	shockType = 0 # type of shock that hits the system in the current state
	
	pBank = 0.0 # bank's assumed credit success probability
	rhoBank = 0.0 # expected return of banks
	thetaBank = 0.0 # bank's risk aversion parameter
	xiBank = 0.0 # scaling factor for CRRA
	gammaBank = 0.0 # fraction of interbank lending in overall balance sheet
	
	assetNumber = 0 # number of assets in the economy
	liquidationDiscountFactor =0.0 # the discount factor delta in exp(-delta x) when liquidating assets
	interbankLoanMaturity = 0.0 # the maturity of interbank loans
	firmLoanMaturity = 0.0 # maturity of loans to firms
	requiredCapitalRatio = 0.08 # the required capital ratio for banks

	#
	# METHODS
	#
	def __init__(self):
		pass

	def print_state(self):
		print "rb: " + str(self.rb)
		print "rd: " + str(self.rd)
		print "r: " + str(self.r)
		print "sifiSurchargeFactor: " + str(self.sifiSurchargeFactor)
		print "successProbabilityFirms: " + str(self.successProbabilityFirms)
		print "positiveReturnFirms: " + str(self.positiveReturnFirms)
		print "scaleFactorHouseholds: " + str(self.scaleFactorHouseholds)
		print "dividendLevel: " + str(self.dividendLevel)
		print "shockType: " + str(self.shockType)
		print "pBank: " + str(self.pBank)
		print "xiBank: " + str(self.xiBank)
		print "thetaBank: " + str(self.thetaBank)
		print "rhoBank: " + str(self.rhoBank)
		print "gammaBank: " + str(self.gammaBank)
		print "assetNumber: " + str(self.assetNumber)
		print "liquidationDiscountFactor: " + str(self.liquidationDiscountFactor)
		print "interbankLoanMaturity: " + str(self.interbankLoanMaturity)
		print "firmLoanMaturity: " + str(self.firmLoanMaturity)
		print "requiredCapitalRatio: " + str(self.requiredCapitalRatio)
