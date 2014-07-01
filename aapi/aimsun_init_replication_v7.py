#
# Start Aimsun 7 simulation of a single replication
#
# Thanks to Nicolas Ditchi and Xin Wuping for pointing out how to modify
# Aimsun extension location programmaticaly. The rest is adopted from
# Aimsun 7 Scripting documentation.
#
# (c) 2013 ÚTIA AVČR
#
# Version: $Id$
#

import sys
import os.path

from PyANGBasic import *
from PyANGKernel import *
from PyANGGui import *
from PyANGAimsun import *

def error_msg(gui,msg,title="Error"):
    """Output an error message either as an alert box or as a simple printout."""
    if gui:
        gui.showMessage(GGui.eCritical, title, msg)
    else:
        print msg

def main(argv):

    # Get the GUI handle. The handle will be None for Aimsun console
    gui = GKGUISystem.getGUISystem().getActiveGui()

    # While `aconsole.exe -script` does not occur in argv[], in case of starting the simulation in GUI
    # mode, first two elements are path to Aimsun.exe and -script command line option.
    gui_param_offset = 2 if gui else 0

    # --------------
    # Input checking
    # --------------
    # Check the number of command line parameters
    if len(argv) != 4+gui_param_offset:
        # As the script is being executed by Aimsun, we have got at least three command line parameters
        error_msg(gui,"Usage: aimsun.exe -script %s NETWORK_NAME REPLICATION_ID SIRID_EXTENSION_PATH" % argv[0+gui_param_offset])
        return -1

    # Check that the replication id is an integer
    try:
        replication_id = int(argv[2+gui_param_offset])
    except ValueError:
        error_msg(gui,"ERROR: Replication id `%s`` is not an integer" % argv[2+gui_param_offset])
        return -1

    # Check that the NETWORK_NAME exists
    network_path = argv[1+gui_param_offset]
    if not os.path.exists(network_path):
        error_msg(gui,"ERROR: Network `%s` does not exist" % network_path)
        return -1

    # Check that the SIRID_EXTENSION_PATH exists
    new_path_sirid = argv[3+gui_param_offset]
    if not os.path.exists(new_path_sirid):
        error_msg(gui,"ERROR: SIRID extension path `%s` does not exist" % new_path_sirid)
        return -1

    if not gui:
        print "ERROR: Aimsun console not yet supported"
        return -1

    # Simulation mode
    # TODO: Add a parameter for this
    mode = GKReplication.eInteractiveAutoPlay

    # --------------
    # Aimsun script
    # --------------

    # Load the network
    if gui.loadNetwork(network_path):
        # Get the handle to the active model of the network
        model = gui.getActiveModel()
        # In order to modify the scenario contents, we need to search for all
        # scenarios by their internal type `GKScenario`
        scenarioType = model.getType( "GKScenario")
        # Get the model catalog
        model_catalog = model.getCatalog()
        # List the scenarios in the active model
        scenarios = model_catalog.getObjectsByType ( scenarioType )
        # Loop over all scenarios
        for scenario in scenarios.itervalues():
            inputdata = scenario.getInputData()
            # The two lines below are used to automatically generate proper paths
            # to the extension DLLs. Do not change them.
            path_sirid = QString ( new_path_sirid )
            # Remove all existing extensions
            inputdata.removeExtensions()
            # And enter the correct path of our AAPI extension and enable it
            inputdata.addExtension ( path_sirid, True )
        # Now we have all scenarios in the model update with correct location of
        # extension DLLs.
        # It is time to simulate the selected replication.
        # The microsimulator is in fact a plug-in module
        micro_plugin = GKSystem.getSystem().getPlugin( "GGetram" )
        # GGetram is the internal plug-in name as found in the XML that describes
        # the plug-in (look in `plugins` folder of the Aimsun installation).
        # Now we ask the plugin to provide us with a simulator
        simulator = micro_plugin.getCreateSimulator( model )
        # Test if the simulator is busy
        # @TODO@ why this?
        if simulator.isBusy() == False :
            # We can use it
            replication = model_catalog.find( replication_id )
            # Check that we have a replication with the specified id
            if replication != None and replication.isA( "GKReplication" ) :
                if replication.getExperiment().getSimulatorEngine() == GKExperiment.eMicro :
                    # TODO: Add support for batch simulation
                    # Add the batch simulation of the selected replication to the
                    # list of tasks that the simulator should simulate
                    # simulator.addSimulationTask (
                    #    GKSimulationTask ( replication, GKReplication.eBatch ))
                    simulator.addSimulationTask (
                        GKSimulationTask ( replication, mode ))
                    # And run the task
                    simulator.simulate()
                else :
                    gui.showMessage (
                        GGui.eCritical,
                        "Simulator error",
                        "The experiment containing replication {0:d} is not microscopic".format(replication_id))
            else :
                gui.showMessage (
                    GGui.eCritical,
                    "Replication error",
                    "The id {0:d} does not exist or it does not define a replication".format(replication_id))
        else :
            gui.showMessage (
                GGui.eCritical,
                "Simulator is busy",
                "The simulator seems to be busy, please start the simulation later")
        # TODO: This would be valid in batch simulation mode but not in interactive mode
        if mode == GKReplication.eBatch:
            # Close the network
            gui.closeDocument ( model )
            # Quit the GUI
            gui.forceQuit()
        else:
            gui.showMessage (
                GGui.eCritical,
                "Simulation is running",
                "Simulation is now running in interactive mode.\n" \
                "Please exit the simulator manually when you are finished.")

    else:
        gui.showMessage (
            GGui.eCritical,
            "Open error",
            "Cannot load the network {0}".format(argv[3]))

main(sys.argv)