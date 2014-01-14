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


#-------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------
if __name__ == '__main__':
	import sys
	sys.path.append('src/')
	from tests import Tests
	
	#
	# VARIABLES
	#
	tests = Tests()
	
	#
	# CODE
	#
	# for each appropriate chunk of the original code we need one test to ensure it is working
	#args=['./netfimas.py',  "test_environments/", "test3",  "log/"]
	#tests.network__do_interbank_trades(args)
	#tests.network__remove_inactive_bank(args)
	#tests.updater__updater1(args)
	#tests.updater__liquidate_assets(args)
	#tests.updater__updater2(args)

	args=['./netfimas.py',  "test_environments/", "test20",  "log/",  "measurements/"]
	args = sys.argv
	tests.test_fire_sales(args)
