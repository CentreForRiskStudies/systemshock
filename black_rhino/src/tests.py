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

import logging

#-------------------------------------------------------------------------
#  class Tests
#-------------------------------------------------------------------------
class Tests(object):
	#
	# VARIABLES
	#
	
	
	# 
	# METHODS
	#
	
	#-------------------------------------------------------------------------
	# __init__
	#-------------------------------------------------------------------------
	def __init__(self):
		pass
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# test_updater1()
	#-------------------------------------------------------------------------
	def updater__updater1(self, args):
		from environment import Environment
		from updater import Updater
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for test updater__updater1 in run: %s',  environment_directory + identifier + ".xml")
		
		#
		# TEST CODE
		#
		environment = Environment(environment_directory,  identifier)
		# create a test environment with standardised banks
		
		print environment.banks[0]
		print environment.banks[1]
		print environment.banks[2]
		
		updater = Updater(environment)
		
		#
		# execute the update code
		#
		updater.do_update_phase1(environment.get_state(0),  environment.network, environment.network.contracts.nodes(), 0, "info")
		
		print environment.banks[0]
		print environment.banks[1]
		print environment.banks[2]
		
		#
		# MEASUREMENT AND LOGGING
		#
		logging.info('FINISHED logging for test updater__updater1 in run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# network__remove_inactive_bank()
	#-------------------------------------------------------------------------
	def network__remove_inactive_bank(self, args):
		from environment import Environment
		from updater import Updater
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for test updater__remove_inactive_banks in run: %s',  environment_directory + identifier + ".xml")
		
		#
		# TEST CODE
		#
		environment = Environment(environment_directory,  identifier)
		# create a test environment with standardised banks
		
		#print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		environment.banks[0].Lp = 2.0
		environment.banks[1].Lp = -1.0
		environment.banks[2].Lp = -1.0
		environment.network.do_interbank_trades(environment.get_state(0))
		print environment.network
		
		updater = Updater(environment)
		
		#
		# execute the update code
		#
		environment.banks[0].reduce_banking_capital(2.0)
		environment.banks[0].check_solvency('info')
		environment.network.remove_inactive_bank(environment.banks[0])
		
		#print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		print environment.network
		
		#
		# MEASUREMENT AND LOGGING
		#
		logging.info('FINISHED logging for test updater__remove_inactive_bank in run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# network__do_interbank_trades(args)
	#-------------------------------------------------------------------------
	def network__do_interbank_trades(self, args):
		from environment import Environment
		from updater import Updater
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for test network__do_interbank_trades in run: %s',  environment_directory + identifier + ".xml")
		
		#
		# TEST CODE
		#
		environment = Environment(environment_directory,  identifier)
		# create a test environment with standardised banks
		
		#print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		print environment.network
		environment.banks[0].Lp = 2.0
		environment.banks[1].Lp = -1.0
		environment.banks[2].Lp = -1.0
		environment.network.do_interbank_trades(environment.get_state(0))
		print environment.network
		environment.banks[0].Lp = 2.3
		environment.banks[1].Lp = -1.1
		environment.banks[2].Lp = -1.2
		environment.network.do_interbank_trades(environment.get_state(0))
		print environment.network
		
		#print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		
		#
		# MEASUREMENT AND LOGGING
		#
		logging.info('FINISHED logging for test updater__remove_inactive_bank in run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# test_updater2()
	#-------------------------------------------------------------------------
	def updater__updater2(self, args):
		from environment import Environment
		from updater import Updater
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for test updater__updater2 in run: %s',  environment_directory + identifier + ".xml")
		
		#
		# TEST CODE
		#
		environment = Environment(environment_directory,  identifier)
		# create a test environment with standardised banks
		environment.banks[0].change_deposits(1.0)
		environment.banks[1].change_deposits(-1.0)
		
		updater = Updater(environment)
		
		#
		# execute the update code
		#
		updater.do_update(environment.get_state(0),  environment.network, environment.network.contracts.nodes(), 0, "info")
		
		#
		# MEASUREMENT AND LOGGING
		#
		logging.info('FINISHED logging for test updater__updater2 in run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# liquidate_assets()
	#-------------------------------------------------------------------------
	def updater__liquidate_assets(self, args):
		from environment import Environment
		from updater import Updater
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for test updater__liquidate_assets in run: %s',  environment_directory + identifier + ".xml")
		
		#
		# TEST CODE
		#
		environment = Environment(environment_directory,  identifier)
		# create a test environment with standardised banks
		
		print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		
		updater = Updater(environment)
		environment.banks[1].active=-1
		environment.banks[2].active=-1
		#
		# execute the update code
		#
		updater.do_update_phase1(environment, 0, "debug")
		updater.do_update_phase2(environment, 0, "info")
		
		print environment.banks[0]
		#print environment.banks[1]
		#print environment.banks[2]
		
		#
		# MEASUREMENT AND LOGGING
		#
		logging.info('FINISHED logging for test updater__liquidate_assets in run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------


	#-------------------------------------------------------------------------
	# test_fire_sales
	#-------------------------------------------------------------------------
	def test_fire_sales(self, args):
		import logging
		import networkx as nx
		
		from environment import Environment
		from runner import Runner
		from measurement import Measurement
		
		#
		# INITIALIZATION
		#
		environment_directory = str(args[1])
		identifier = str(args[2])
		log_directory = str(args[3])
		measurement_directory = str(args[4])
		
		# Configure logging parameters so we get output while the program runs
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',  filename = log_directory + identifier + ".log", level=logging.INFO)
		logging.info('START logging for run: %s',  environment_directory + identifier + ".xml")
		
		environment = Environment()
		environment.initialize(environment_directory,  identifier)
		runner = Runner()
		measurement = Measurement()
		
		#
		# UPDATE STEP
		#
		for i in range(environment.parameters.numSimulations):
			environment.initialize(environment_directory,  identifier)
			runner.initialize(environment)
			measurement.initialize() # clear the previous measurement
			
			# do the run
			runner.do_run(measurement, "info")
			
			# do the histograms, i.e. add the current measurement to the histogram
			measurement.do_histograms()
			logging.info('')
		
		#
		# MEASUREMENT AND LOGGING
		#
		measurement.write_histograms(measurement_directory,  environment)
		logging.info('FINISHED logging for run: %s \n', environment_directory + identifier + ".xml")
	#-------------------------------------------------------------------------
