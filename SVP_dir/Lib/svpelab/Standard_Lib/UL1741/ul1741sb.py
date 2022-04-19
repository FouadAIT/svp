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

import os
from svpelab.Standard_Lib.function_layer import InitializationLayer
from svpelab.Standard_Lib.UL1741 import postprocess
from svpelab import gridsim
from svpelab import pvsim
from svpelab import das
from svpelab import der
from svpelab import hil
from svpelab import result as rslt
#from svpelab.Standard_Lib import standard_datapoints
from svpelab.Standard_Lib.datalogging import DataLogging


UL1741SB_DEFAULT_ID = 'UL1741SB'


class UL1741Error(Exception):
    pass


def params(info, group_name=None, label='UL1741SB'):
    group_name = UL1741SB_DEFAULT_ID
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label=f'{label} Parameters', glob=True)

    #Automatic=Postprocessing will be ran automatically after the script is completed
    #Manual=Postprocessing will be ran independant from script based on previous results
    info.param(name('pp_ena'), label='Postprocessing', default='Disabled', values=['Enabled', 'Manual', 'Disabled'])
    info.param(name('file_location'), label='Results file location', default='/RESULT-FILES-LOCATIONS/HERE', active=name('pp_ena'), active_value=['Manual'])
    info.param(name('test_name'), label='Test name', default='Volt-Watt', values=['Volt-Watt', 'Volt-Var'], active=name('pp_ena'), active_value=['Manual'])
    #info.param(name('curve'), label='Curve selection', default='curve1', values=['curve1', 'curve2', 'curve3'], active=name('pp_ena'), active_value=['Manual'])

class ActiveFunction(ExtractDatapoints):
    def __init__(self, ts, function=None, standard='UL1741SB'):
        #Import UL1741 standard curve points
        #UL1741 uses the same points as IEEE1547.1
        ts.log_debug(f'FUNCTION1={function}')
        super().__init__(ts=ts, standard=standard, function=function)

        self.pp_ena = self.ts.param_value('UL1741SB.pp_ena')

        self.curve = None
        self.cat = 'Category B'
        self.pwr = None
        self.step_label = None
        self.steps_dict = None
        self.chil = None
        self.pv = None
        self.eut = None
        self.grid = None
        self.full_name_unit = {
            'V': 'Voltage',
            'P': 'Active Power',
            'Q': 'Reactive Power',
            'F': 'Frequency',
            'PF': 'Power Factor',
            'I': 'Current'
            }
        #if function == 'Volt-Watt':
            #self.ts.log_debug(50*'(_+_)')
            #from svpelab.Standard_Lib.IEEE1547.GridSupportFunction.VoltWatt import create_dict_steps
            #self.step_dict = self.create_dict_steps()
    def eut_init(self):
        """Eut initialization
        """
        if self.chil is not None:
            self.ts.log('Start simulation of CHIL')
            self.chil.start_simulation()
            self.ts.log('10 seconds start up')
            self.ts.sleep(10)

        self.ts.log_debug(15*"*"+"EUT initialization"+15*"*")
        self.eut = der.der_init(self.ts, support_interfaces={'hil': self.chil})
        if self.eut is None:
            der.DERError(f'EUT is None')
        
        #self.v_nom = self.eut.v_nom()
        if self.eut is not None:
            self.s_rated = self.eut.s_rated()
            self.v_max = self.eut.v_high()
            self.v_min = self.eut.v_low()
            self.v_in_nom = self.eut.v_in_nom()
            self.eut_startup_time = self.eut.startup_time()
            self.p_rated = self.eut.p_rated()
            self.phases = self.eut.phase()

            self.MRA = {
                'V': 0.01 * self.v_nom,
                'Q': 0.05 * self.s_rated,
                'P': 0.05 * self.s_rated,
                'F': 0.01,
                'T': 0.01,
                'PF': 0.01
            }


            self.ts.log(f'{self.eut_startup_time} seconds EUT start up')
            self.ts.sleep(self.eut_startup_time)
            self.eut.config()
            self.ts.log_debug(self.eut.measurements())
            self.ts.log_debug(
                'L/HVRT and trip parameters set to the widest range : v_min: {0} V, v_max: {1} V'.format(self.v_min, self.v_max))
            try:
                self.eut.vrt_stay_connected_high(
                    params={'Ena': True, 'ActCrv': 0, 'Tms1': 3000, 'V1': self.v_max, 'Tms2': 0.16, 'V2': self.v_max})
            except Exception as e:
                self.ts.log_error('Could not set VRT Stay Connected High curve. %s' % e)
            try:
                self.eut.vrt_stay_connected_low(
                    params={'Ena': True, 'ActCrv': 0, 'Tms1': 3000, 'V1': self.v_min, 'Tms2': 0.16, 'V2': self.v_min})
            except Exception as e:
                self.ts.log_error('Could not set VRT Stay Connected Low curve. %s' % e)

        else:
            self.ts.log_debug('Set L/HVRT and trip parameters set to the widest range of adjustability possible.')


    def chil_init(self):
        """HIL initialization function
        """
        self.ts.log_debug(15*"*"+"HIL initialization"+15*"*")
        self.chil = hil.hil_init(self.ts)
        if self.chil is not None:
            self.chil.config()

    def gridsim_init(self):
        """Initialize GRIDSIM function
        """
        self.v_nom = self.ts.param_value('der.v_nom')

        self.ts.log_debug(15*"*"+"GRIDSIM initialization"+15*"*")
        grid = gridsim.gridsim_init(self.ts,support_interfaces={'hil': self.chil})  # Turn on AC so the EUT can be initialized
        if grid is not None:
            grid.voltage(self.v_nom)
            if self.chil is not None:  # If using HIL, give the grid simulator the hil object
                grid.config()

    def set_grid_nom(self):
        #Setting grid to vnom before test
        if self.grid is not None:
            self.grid.voltage(self.v_nom)


    def pv_init(self):

        self.ts.log_debug(15*"*"+"PVSIM initialization"+15*"*")
        self.pv = pvsim.pvsim_init(self.ts, support_interfaces={'hil': self.chil})
        if self.pv is not None:
            self.pv.power_set(self.p_rated)
            self.pv.power_on()  # Turn on DC so the EUT can be initialized
            self.ts.sleep(0.5)

    def set_dc_pwr(self, irr, pwr=None):
        if self.pv is not None:
            if pwr is None:
                pv_power_setting = self.p_rated * self.pwr
            else:
                pv_power_setting = self.p_rated * pwr

            self.pv.iv_curve_config(pmp=pv_power_setting, vmp=self.v_in_nom)
            self.pv.irradiance_set(irr)

    def execute_postprocess(self):
        """This function will initiate the post-processing depending 
        if it is enabled or not
        """
        self.pp_dict = {
            'Volt-Var': True,
            'Volt-Watt': True
            }

        if self.pp_ena == 'Manual':

            if self.test_name is None:
                self.test_name = self.ts.param_value('UL1741SB.test_name')
            self.file_location = self.ts.param_value('UL1741SB.file_location')

        if self.pp_ena == 'Enabled' or self.pp_ena == 'Manual':

            self.ts.log_debug(f'Test Name set to {self.test_name}')
            self.ts.log_debug(f'Postprocessing set at {self.pp_ena}')

            if self.test_name in self.pp_dict:
                #IEEE1547_dict = self.IEEE1547_obj.import_curvepoints(self.test_name)
                self.ts.log_debug('Postprocessing Starting')
                #self.standard_dict from ExtractDatapoints
                ul1741pp = postprocess.UL1741postprocessing(self.ts, self.standard_dict)
            else:
                self.ts.log_debug('Postprocessing is not available for this script test')
        elif self.pp_ena == 'Disabled': 
            self.ts.log_debug('Postprocessing is disabled')

    def set_pwr_setting(self, pwr):
        self.pwr = pwr

    def set_curve(self, curve):
        """Set desired curve if there is any

        Parameters
        ----------
        curve : int
        """
        self.curve = curve
    
    def set_category(self, category='Category B'):
        """Set Category type for the script function
        Keep in mind that the curve point must be present in the JSON files
        Value is defaulted to Category B for now.

        Parameters
        ----------
        category : String
            Must be either Category B or Category A
        """
        self.cat = category

    def create_logger(self, result_summary=None):
        self.logger = DataLogging(ts=self.ts, standard_dict=self.standard_dict, support_interfaces={'hil': self.chil})
        self.result_params = self.logger.get_rslt_param_plot()
        if result_summary is not None:
            result_summary.write(self.logger.get_rslt_sum_col_name())

    def set_time_settings(self, tr, number_tr):
        self.tr = tr
        self.number_tr = number_tr
        self.logger.set_time_settings(tr, number_tr)

    def start_recording(self):
        self.logger.data_capture(True)

    def stop_recording(self):
        self.logger.data_capture(False)

    def create_dataset_filename(self):
        dataset_filename = self.ts.name.split('.')[0]
        if self.curve is not None:
            dataset_filename += f'_{self.curve}'
        if self.pwr is not None:
            dataset_filename += f'_{int(self.pwr*100)}'
        dataset_filename += '.csv'
        return dataset_filename

    def save_recording(self):

        self.result_params = self.logger.get_rslt_param_plot()
        ds = self.logger.data_capture_dataset()
        self.ts.log('Saving file: %s' % self.dataset_filename)
        ds.to_csv(self.ts.result_file_path(self.dataset_filename))
        self.result_params['plot.title'] = self.dataset_filename.split('.csv')[0]
        self.ts.result_file(self.dataset_filename, params=self.result_params)   

    def execute_test_procedure_steps(self, result_summary):
        if self.steps_dict is None:
            raise self.ts.log_error('Steps dictionary is not initialized')

        for step_label, step_dict in self.steps_dict.items():

            if 'V' in step_dict:
                self.ts.log('Voltage step: setting Grid simulator voltage to %s (%s)' % (step_dict['V'], step_label))            
                if self.grid is not None:
                    self.grid.voltage(step_dict['V'])
            if 'F' in step_dict:
                pass
            if 'PF' in step_dict:
                pass
            if 'P' in step_dict:
                pass

            self.logger.record_timeresponse(step_dict, step_label)
            self.dataset_filename = self.create_dataset_filename()
            self.logger.set_filename(self.dataset_filename)
            data = self.logger.write_rslt_sum()
            result_summary.write(data)

    def close(self):
        if self.pv is not None:
            if self.p_rated is not None:
                self.pv.power_set(self.p_rated)
            self.pv.close()
        if self.grid is not None:
            if self.v_nom is not None:
                self.grid.voltage(self.v_nom)
            self.grid.close()
        if self.chil is not None:
            self.chil.close()
        if self.eut is not None:
            self.eut.close()


    from svpelab.Standard_Lib._utlity import set_step_label, get_step_label
    #VOLT-WATT GRIDSUPPORTFUNCTION
    from svpelab.Standard_Lib.IEEE1547.GridSupportFunction._VoltWatt import create_vw_dict_steps, vw_config_to_eut

if __name__ == "__main__":
    pass