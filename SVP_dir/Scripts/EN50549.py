import sys
import os
import traceback
from svpelab import gridsim
from svpelab import pvsim
from svpelab import das
from svpelab import der
from svpelab import hil
from svpelab import result as rslt
from svpelab.Standard_Lib.EN50549.GridSupportFunction.volt_watt_layer import VoltWatt
from svpelab.Standard_Lib.EN50549.GridSupportFunction.volt_var_layer import VoltVar
from svpelab.Standard_Lib.EN50549.GridSupportFunction.freq_watt_layer import FreqWatt

from svpelab.Standard_Lib.EN50549 import EN50549_layer

from datetime import datetime, timedelta
import script
import math
import numpy as np
import collections
import cmath

FW = 'FW'
CPF = 'CPF'
VW = 'VW'
VV = 'VV'
WV = 'WV'
CRP = 'CRP'
PRI = 'PRI'
LFRT = "LFRT"
HFRT = "HFRT"
LV = 'LV'
HV = 'HV'
CAT_2 = 'CAT_2'
CAT_3 = 'CAT_3'

IEEE_FILENAME = 'EN50549-10_summary.csv'

def test_run():
    result = script.RESULT_FAIL

    try:
        result = script.RESULT_FAIL
        result_summary = None
        dataset_filename = None
        ActiveFunction = None
        Imbalance_test = None
        imbalance_resp = [1]
        imbalance_fix = None

        """
        A separate module has been create for the 1547.1 Standard
        """
        if ts.param_value('EN50549.gsf') == "VW":
            ActiveFunction = VoltWatt(ts)
        if ts.param_value('EN50549.gsf') == "VV":
            ActiveFunction = VoltVar(ts)
        if ts.param_value('EN50549.gsf') == "FW":
            ActiveFunction = FreqWatt(ts)

        ActiveFunction.log_debug("EN50549-10 Library configured for %s" % ActiveFunction.get_script_name())

        '''
        a) Connect the EUT according to the instructions and specifications provided by the manufacturer.
        '''
        # Initialize HIL
        ActiveFunction.chil_init()

        # Start the HIL simulation
        # TODO : Add a condition to know when you are in PHIL, CHIL or SIL mode.
        #        Depending of the mode the .chil_start_simulation() need to be earlier or later.
        #ActiveFunction.chil_start_simulation()

        # Initialize grid simulator
        ActiveFunction.grid_init()

        # Initialize the equipment under test (EUT)
        ActiveFunction.eut_init()

        # Initialize the pv simulator
        ActiveFunction.pv_init()

        # Added this to perform the test with full power
        ts.sleep(30)
        '''
        c) Set all AC test source parameters to the nominal operating voltage and frequency.
        '''
        ActiveFunction.set_grid_to_nominal()

        # open result summary file
        ActiveFunction.create_result_summary()


        # DAS soft channels
        # initialize data acquisition system
        ActiveFunction.create_logger()

        '''
        v) Test may be repeated for EUT's that can also absorb power using the P' values in the characteristic
        definition.
        '''

        '''
        u) Repeat steps d) through u) for characteristics 2 and 3.
        '''
        test_procedure_loops = ActiveFunction.create_configuration_variables()
        ts.log(f'test_procedure_loops =  {test_procedure_loops}')

        #If using SIL start simulation here
        #ActiveFunction.chil_start_simulation()

        for loop in test_procedure_loops:
            ActiveFunction.set_loop_test_procedure_configuration(loop)
            ts.log(f'Starting loop {loop}')
            ts.log(f'Test procedure curve (if any) {ActiveFunction.get_curve()}')
            ts.log(f'Test procedure power level (if any) {ActiveFunction.get_pwr()}')
            steps = ActiveFunction.create_dict_steps()
            '''
            t) Repeat steps d) through t) at EUT power set at 20% and 66% of rated power.
            '''
            ActiveFunction.set_test_bench_equipment()

            '''
            d) Adjust the EUT's available active power to Prated. For an EUT with an input voltage range, set the input
            voltage to Vin_nom. The EUT may limit active power throughout the test to meet reactive power requirements.
            For an EUT with an input voltage range.
            '''


            '''
            Refer to P1547 Library and IEEE1547.1 standard for steps
            '''
            # Initiate recording
            ActiveFunction.start_recording()
            # Start test procedure
            ActiveFunction.execute_test_procedure_steps()

            # create result workbook
            ts.log('Sampling complete')
            ActiveFunction.stop_recording()
            ActiveFunction.save_recording()

            ActiveFunction.execute_postprocess(steps)

        """
        if ActiveFunction is not None:
            ActiveFunction.execute_postprocess()
        """


        result = script.RESULT_COMPLETE


    except Exception as e:
        ActiveFunction.finish_test()
        reason = str(e)
        ts.log_error(reason)
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        raise

    except script.ScriptFail as e:
        reason = str(e)
        ActiveFunction.finish_test()
        if reason:
            ts.log_error(reason)

    finally:
        # create result workbook
        excelfile = ts.config_name() + '.xlsx'
        rslt.result_workbook(excelfile, ts.results_dir(), ts.result_dir())
        ts.result_file(excelfile)
        if ActiveFunction is not None:
            ActiveFunction.finish_test()
            ActiveFunction.close_all_equipments()


    return result


def run(test_script):

    try:
        global ts
        ts = test_script
        rc = 0
        result = script.RESULT_COMPLETE

        ts.log_debug('')
        ts.log_debug('**************  Starting %s  **************' % (ts.config_name()))
        ts.log_debug('Script: %s %s' % (ts.name, ts.info.version))
        ts.log_active_params()

        result = test_run()

        ts.result(result)
        if result == script.RESULT_FAIL:
            rc = 1

    except Exception as e:
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        rc = 1

    sys.exit(rc)

info = script.ScriptInfo(name=os.path.basename(__file__), run=run, version='2.0.0')
"""
Volt-Watt Parameters
"""
info.param_group('EN50549', label='Grid Support Function (GSF) following EN50549-10:2021')
info.param('EN50549.gsf', label='Which GSF to test ?', default='VV', values=['VV','VW','FW'])

info.param_group('vv', label='Volt-Var Test Parameters',active='EN50549.gsf', active_value="VV")
info.param('vv.mode', label='Volt-Var mode', default='Normal', values=['Normal'],active='EN50549.gsf', active_value="VV")
info.param('vv.test_1', label='Characteristic 1 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='vv.mode', active_value=['Normal', 'Imbalanced grid'])
info.param('vv.test_1_tr', label='Response time (s) for curve 1', default=10.0,
           active='vv.test_1', active_value=['Enabled'])
info.param('vv.test_2', label='Characteristic 2 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='vv.mode', active_value=['Normal'])
info.param('vv.test_2_tr', label='Response time (s) for curve 2', default=60.0,
           active='vv.test_2', active_value=['Enabled'])
info.param('vv.power_lvl', label='Power Levels', default='All', values=['100%', '66%', '20%', 'All'],
           active='vv.mode', active_value=['Normal'])
info.param('vv.state', label='State behaviour of the test procedure', default='Steady', values=['Steady', 'Dynamic'],
           active='vv.mode', active_value=['Normal'])

info.param_group('vw', label='Volt-Watt Test Parameters',active='EN50549.gsf', active_value="VW")
info.param('vw.mode', label='Volt-Watt mode', default='Normal', values=['Normal'],active='EN50549.gsf', active_value="VW")
info.param('vw.test_1', label='Characteristic 1 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='vw.mode', active_value=['Normal', 'Imbalanced grid'])
info.param('vw.test_1_tr', label='Response time (s) for curve 1', default=10.0,
           active='vw.test_1', active_value=['Enabled'])
info.param('vw.test_2', label='Characteristic 2 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='vw.mode', active_value=['Normal'])
info.param('vw.test_2_tr', label='Response time (s) for curve 2', default=60.0,
           active='vw.test_2', active_value=['Enabled'])
info.param('vw.test_3', label='Characteristic 3 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='vw.mode', active_value=['Normal'])
info.param('vw.test_3_tr', label='Response time (s) for curve 3', default=0.5,
           active='vw.test_3', active_value=['Enabled'])
info.param('vw.power_lvl', label='Power Levels', default='All', values=['100%', '66%', '20%', 'All'],
           active='vw.mode', active_value=['Normal'])
#info.param('vw.ul1741_ena', label='Activate UL1741 post processing after test is completed?',
#           values=['Yes', 'No'], default='No')
#info.param('vw.imbalance_fix', label='Use minimum fix requirements from Table 24?',
#           default='std', values=['fix_mag', 'fix_ang','std', 'not_fix'], active='vw.mode', active_value=['Imbalanced grid'])
info.param('vw.state', label='State behaviour of the test procedure', default='Steady', values=['Steady', 'Dynamic'],
           active='vw.mode', active_value=['Normal'])


info.param_group('fw', label='Freq-Watt Test Parameters',active='EN50549.gsf', active_value="FW")
info.param('fw.mode', label='Freq-Watt mode', default='Normal', values=['Normal'],active='EN50549.gsf', active_value="FW")
info.param('fw.behaviour', label='Frequency-Watt type of test', default='Above', values=['Above', 'Under'],
           active='fw.mode', active_value=['Normal'])
info.param('fw.test_1', label='Characteristic 1 curve', default='Enabled', values=['Disabled', 'Enabled'],
           active='fw.behaviour', active_value=['Above'])
info.param('fw.test_1_tr', label='Response time (s) for curve 1', default=30.0,
           active='fw.test_1', active_value=['Enabled'])
info.param('fw.test_1_droop', label='Droop of the active power [%]',default=10.0, values=[5.0, 2.0, 12.0],
           active='fw.test_1', active_value=['Enabled'])
info.param('fw.power_lvl', label='Power Levels', default='All', values=['100%', '66%', '20%', 'All'],
           active='fw.mode', active_value=['Normal'])


# Other equipment parameters
EN50549_layer.params(info)
der.params(info)
gridsim.params(info)
pvsim.params(info)
das.params(info)
hil.params(info)

# Add the SIRFN logo
info.logo('sirfn.png')

def script_info():

    return info


if __name__ == "__main__":

    # stand alone invocation
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    params = None

    test_script = script.Script(info=script_info(), config_file=config_file, params=params)
    test_script.log('log it')

    run(test_script)