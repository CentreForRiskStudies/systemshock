__author__ = 'Louise'

import sys
import cProfile
import simulator
import utils


def run_simulation(paramFile, paramsDir="parameters/"):
    pList, basicGraph = utils.read_params_file(paramsDir, paramFile)
    simulator.setup_simulation(pList, basicGraph)


#-----------------------------------------------------------------------------------------------
if __name__ == '__main__':

    args = sys.argv

    if len(args) < 2:
        print "Must specify parameter file"
        sys.exit()

    if len(args) >= 3 and str(args[2]) == "-p":  # do profiling
        statement = "run_simulation('" + str(args[1]) + "')"
        cProfile.run(statement, 'logs/profstats')
    else:
        run_simulation(str(args[1]))
