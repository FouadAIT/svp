"""
Copyright (c) 2018, Sandia National Labs, SunSpec Alliance and CanmetENERGY(Natural Resources Canada)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs, SunSpec Alliance and CanmetENERGY(Natural Resources Canada)
nor the names of its contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Questions can be directed to support@sunspec.org
"""

import sys
import os
import traceback
from svpelab import gridsim
from svpelab import pvsim
from svpelab import das
from svpelab import der
from svpelab import hil
from svpelab import result as rslt
from svpelab.Standard_Lib.IEEE1547.GridSupportFunction.volt_watt_layer import VoltWatt
from svpelab.Standard_Lib.IEEE1547.GridSupportFunction.voltage_ride_through_layer import VoltageRideThrough

from svpelab.Standard_Lib.IEEE1547 import IEEE1547_layer

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

IEEE_FILENAME = 'IEEE1547-1_summary.csv'

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
        if ts.param_value('ieee1547.gsf') == "VW":
            ActiveFunction = VoltWatt(ts)
        elif ts.param_value('ieee1547.gsf') == "VRT":
            ActiveFunction = VoltageRideThrough(ts)


        ActiveFunction.log_debug("1547.1 Library configured for %s" % ActiveFunction.get_script_name())

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
        ActiveFunction.chil_start_simulation()

        for loop in test_procedure_loops:
            ActiveFunction.set_loop_test_procedure_configuration(loop)
            ts.log(f'Starting loop {loop}')
            ts.log(f'Test procedure curve (if any) {ActiveFunction.get_curve()}')
            ts.log(f'Test procedure power level (if any) {ActiveFunction.get_pwr()}')
            ActiveFunction.create_dict_steps()
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

        if ActiveFunction is not None:
            ActiveFunction.execute_postprocess()

        result = script.RESULT_COMPLETE


    except Exception as e:
        reason = str(e)
        ts.log_error(reason)
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        raise

    except script.ScriptFail as e:
        reason = str(e)
        if reason:
            ts.log_error(reason)

    finally:
        # create result workbook
        excelfile = ts.config_name() + '.xlsx'
        rslt.result_workbook(excelfile, ts.results_dir(), ts.result_dir())
        ts.result_file(excelfile)
        if ActiveFunction is not None:
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
info.param_group('ieee1547', label='Grid Support Function (GSF) following IEEE1547.1-2020')
info.param('ieee1547.gsf', label='Which GSF to test ?', default='VW', values=['VW', 'VRT'])
info.param_group('vw', label='Volt-Watt Test Parameters',active='ieee1547.gsf', active_value="VW")
info.param('vw.mode', label='Volt-Watt mode', default='Normal', values=['Normal', 'Imbalanced grid'],active='ieee1547.gsf', active_value="VW")
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
info.param('vw.imbalance_fix', label='Use minimum fix requirements from Table 24?',
           default='std', values=['fix_mag', 'fix_ang','std', 'not_fix'], active='vw.mode', active_value=['Imbalanced grid'])

"""
Voltage Ride-Through Parameters
"""

# PRI test parameters
info.param_group('vrt', label='Voltage Ride-Through Parameters',active='ieee1547.gsf', active_value="VRT")
info.param('vrt.lv_ena', label='Low Voltage mode settings:', default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.hv_ena', label='High Voltage mode settings:', default='Enabled', values=['Disabled', 'Enabled'])

info.param('vrt.low_pwr_ena', label='Low Power Output Test:', default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.low_pwr_value', label='Low Power Output level (Between 25-50%):', default=0.5, active='vrt.low_pwr_ena',
           active_value='Enabled')
info.param('vrt.high_pwr_ena', label='High Power Output Test :', default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.high_pwr_value', label='High Power Output level (Over 90%):', default=0.91, active='vrt.high_pwr_ena',
           active_value='Enabled')
info.param('vrt.cat', label='Category II and/or III:', default=CAT_2, values=[CAT_2, CAT_3, "Both"])
# TODO: The consecutive option needs a way to verify the first test to apply a different perturbation accordingly.
info.param('vrt.consecutive_ena', label='Consecutive Ride-Through test?', default='Enabled',
           values=['Disabled', 'Enabled'])

info.param('vrt.one_phase_mode', label="Apply disturbance to one phase" , default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.one_phase_value', label="Which phase ?" , active='vrt.one_phase_mode', active_value=['Enabled'], default='A', values=['A', 'B', 'C'])

info.param('vrt.two_phase_mode', label="Apply disturbance to two phases" , default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.two_phase_value_1', label="Which phase ?" , active='vrt.two_phase_mode', active_value=['Enabled'], default='A', values=['A', 'B', 'C'])
info.param('vrt.two_phase_value_2', label="Which phase ?" , active='vrt.two_phase_mode', active_value=['Enabled'], default='B', values=['A', 'B', 'C'])
info.param('vrt.three_phase_mode', label="Apply disturbance to all phases" , default='Enabled', values=['Disabled', 'Enabled'])
info.param('vrt.range_steps', label='Ride-Through Profile ("Figure" is following the RT images from standard)',
           default='Figure', values=['Figure', 'Random'])
#info.param('vrt.wav_ena', label='Waveform acquisition needed (.mat->.csv) ?', default='Yes', values=['Yes', 'No'])
#info.param('vrt.data_ena', label='RMS acquisition needed (SVP creates .csv from block queries)?', default='No', values=['Yes', 'No'])

# Other equipment parameters
IEEE1547_layer.params(info)
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
