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
from svpelab.Standard_Lib.UL1741.GridSupportFunction.volt_watt_layer import VoltWatt
from svpelab.Standard_Lib.UL1741 import UL1741SB_layer

from datetime import datetime, timedelta
import script
import math
import numpy as np
import collections
import cmath

#VW = 'VW'
#V = 'V'
#F = 'F'
#P = 'P'
#Q = 'Q'
UL1741_FILENAME = 'UL1741_summary.csv'


def volt_watt_mode(vw_curves, vw_response_time, pwr_lvls, imbalance_test=False):

    result = script.RESULT_FAIL
    result_summary = None
    dataset_filename = None
    ActiveFunction = None
    Imbalance_test = None
    imbalance_resp = [1]
    imbalance_fix = None
    try:


        if imbalance_test:
            imbalance_fix = ts.param_value('vw.imbalance_fix')
            ts.log_debug(f'imbalance fix VW ={imbalance_fix}')
        ActiveFunction = VoltWatt(ts, imbalance_angle_fix=imbalance_fix)
        ActiveFunction.log_debug("Library configured for %s" % ActiveFunction.get_script_name())

        '''
        a) Connect the EUT according to the instructions and specifications provided by the manufacturer.
        '''
        # Initialize HIL
        ActiveFunction.chil_init()

        # Start the HIL simulation
        ActiveFunction.chil_start_simulation()

        # Initialize GRIDSIM
        ActiveFunction.gridsim_init()

        # Initialize the equipment under test (EUT)
        ActiveFunction.eut_init()

        # Initialize the pv simulator
        ActiveFunction.pv_init()

        if imbalance_test:
            imbalance_fix = ts.param_value('vw.imbalance_fix')
            imbalance_resp = ActiveFunction.imbalance_resp()
            ts.log(f'Test has been set to imbalanced mode')
            ts.log(f'Imbalance angle has been set to {imbalance_fix}')


        '''
        c) Set all AC test source parameters to the nominal operating voltage and frequency.
        '''
        ActiveFunction.set_grid_nom()

        # open result summary file
        ActiveFunction.create_result_summary()
        #result_summary = open(ts.result_file_path(IEEE_FILENAME), 'a+')
        #ts.result_file(IEEE_FILENAME)
        #Create empty file for UL1741 result summary to keep this order. The newer file will overwrite this
        """
        if ActiveFunction is not None:
            ul1741_result_summary = open(ts.result_file_path(UL1741_FILENAME), 'a+')
            ts.result_file(UL1741_FILENAME)
            ul1741_result_summary.close()
        """

        # DAS soft channels
        # initialize data acquisition system
        ActiveFunction.create_logger()

        '''
        v) Test may be repeated for EUT's that can also absorb power using the P' values in the characteristic
        definition.
        '''
        # TODO: add P' tests (Like CPF -> for absorb_power in absorb_powers:)

        '''
        u) Repeat steps d) through u) for characteristics 2 and 3.
        '''
        for imb_resp in imbalance_resp:
            if imbalance_test:
                ActiveFunction.set_imbalance_config(imbalance_angle_fix=imbalance_fix, imbalance_resp=imb_resp)
            for vw_curve in vw_curves:
                ts.log('Starting test with characteristic curve %s' % (vw_curve))
                ActiveFunction.set_curve(vw_curve)
                ActiveFunction.set_time_settings(tr=vw_response_time[vw_curve], number_tr=4)
                ActiveFunction.create_dict_steps()
                '''
                t) Repeat steps d) through t) at EUT power set at 20% and 66% of rated power.
                '''
                for power in pwr_lvls:
                    # Configure the data acquisition system
                    ts.log('Starting data capture for power = %s' % power)
                    
                    ActiveFunction.set_pwr_setting(pwr=power)
                    #Setting grid to vnom before test
                    ActiveFunction.set_grid_nom()

                    '''
                    d) Adjust the EUT's available active power to Prated. For an EUT with an input voltage range, set the input
                    voltage to Vin_nom. The EUT may limit active power throughout the test to meet reactive power requirements.
                    For an EUT with an input voltage range.
                    '''
                    ActiveFunction.set_dc_pwr(irr=1100, pwr=power)
                    
                    #Send settings to EUT
                    ActiveFunction.vw_config_to_eut()

                    '''
                    Refer to P1547 Library and IEEE1547.1 standard for steps
                    '''
                    #Initiate recording
                    ActiveFunction.start_recording()
                    #Start test procedure
                    ActiveFunction.execute_test_procedure_steps()

                    # create result workbook
                    ts.log('Sampling complete')
                    ActiveFunction.stop_recording()
                    ActiveFunction.save_recording()

        #Initiate post processing for UL1741SB moving average
        if ActiveFunction is not None:
            ActiveFunction.execute_postprocess()

        result = script.RESULT_COMPLETE


    except Exception as e:
        #if dataset_filename is not None:
        #    dataset_filename = dataset_filename + ".csv"

        # if ActiveFunction is not None:
        #     ActiveFunction.stop_recording()
        #     ActiveFunction.save_recording()
        reason = str(e)
        ts.log_error(reason)
        ts.log_error('Test script exception: %s' % traceback.format_exc())
        raise

    finally:
        if ActiveFunction is not None:
            ActiveFunction.close_all_equipments()
        #if result_summary is not None:
        #    result_summary.close()

    return result


def test_run():

    result = script.RESULT_FAIL

    try:
        """
        Configuration
        """

        # Initialize VW EUT specified parameters variables
        mode = ts.param_value('vw.mode')
        """
        Test Configuration
        """
        # list of active tests
        vw_curves = []
        imbalance_test = False
        vw_response_time = [0, 0, 0, 0]
        if mode == 'Imbalanced grid':
            """
            imbalance_resp = []
            if ts.param_value('eut.imbalance_resp') == 'EUT response to the individual phase voltages':
                imbalance_resp.append('INDIVIDUAL_PHASES_VOLTAGES')
            elif ts.param_value('eut.imbalance_resp') == 'EUT response to the average of the three-phase effective (RMS)':
                imbalance_resp.append('AVG_3PH_RMS')
            else:  # 'EUT response to the positive sequence of voltages'
                imbalance_resp.append('POSITIVE_SEQUENCE_VOLTAGES')
            """
            imbalance_test= True
            vw_curves.append(1)
            vw_response_time[1] = float(ts.param_value('vw.test_1_tr'))

        else:
            if ts.param_value('vw.test_1') == 'Enabled':
                vw_curves.append(1)
                vw_response_time[1] = float(ts.param_value('vw.test_1_tr'))
            if ts.param_value('vw.test_2') == 'Enabled':
                vw_curves.append(2)
                vw_response_time[2] = float(ts.param_value('vw.test_2_tr'))
            if ts.param_value('vw.test_3') == 'Enabled':
                vw_curves.append(3)
                vw_response_time[3] = float(ts.param_value('vw.test_3_tr'))

        # List of power level for tests
        irr = ts.param_value('vw.power_lvl')
        if irr == '20%':
            pwr_lvls = [0.20]
        elif irr == '66%':
            pwr_lvls = [0.66]
        elif irr == '100%':
            pwr_lvls = [1.00]
        elif irr == 'All':
            pwr_lvls = [1.00, 0.66, 0.20]
        else:
            pwr_lvls = [1.00]
        
        result = volt_watt_mode(vw_curves=vw_curves, vw_response_time=vw_response_time, pwr_lvls=pwr_lvls, imbalance_test=imbalance_test)


        return result

    except script.ScriptFail as e:
        reason = str(e)
        if reason:
            ts.log_error(reason)

    finally:
        # create result workbook
        excelfile = ts.config_name() + '.xlsx'
        rslt.result_workbook(excelfile, ts.results_dir(), ts.result_dir())
        ts.result_file(excelfile)


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

# VW test parameters
info.param_group('vw', label='Test Parameters')
info.param('vw.mode', label='Volt-Watt mode', default='Normal', values=['Normal', 'Imbalanced grid'])
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

# Other equipment parameters
UL1741SB_layer.params(info)
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
