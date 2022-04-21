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
from svpelab.Standard_Lib.IEEE1547.post_process import IEEE1547postprocessing
from svpelab.Standard_Lib.function_layer import InitializationLayer
from svpelab.Standard_Lib.datalogging import DataLogging
from svpelab.Standard_Lib.IEEE1547.imbalance_component import ImbalanceComponent
import svpelab.Standard_Lib._utlity as util


IEEE1547_DEFAULT_ID = "IEEE1547dot1"
def params(info, group_name=None, label='IEEE1547.1_LAYER'):
    group_name = IEEE1547_DEFAULT_ID
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label=f'{label} Parameters')

    # Automatic=Postprocessing will be ran automatically after the script is completed
    # Manual=Postprocessing will be ran independant from script based on previous results
    info.param(name('test_name'), label='Test name', default='Volt-Watt', values=['Volt-Watt', 'Volt-Var'],
               active=name('pp_ena'), active_value=['Manual'])
    info.param(name('pp_ena'), label='Postprocessing', default='Disabled', values=['Enabled', 'Manual', 'Disabled'])
    info.param(name('file_location'), label='Results file location', default='/RESULT-FILES-LOCATIONS/HERE',
               active=name('pp_ena'), active_value=['Manual'])


class IEEE1547dot1Layer(InitializationLayer, ImbalanceComponent):
    def __init__(self, ts, function=None):
        self.standard = 'IEEE1547dot1'
        #EquipmentsManager.__init__(ts)
        super(IEEE1547dot1Layer, self).__init__(ts=ts, standard=self.standard, function=function)
        self.function = function
        self.curve = None
        self.cat = 'Category B'
        self.pwr = None
        self.step_label = None
        self.steps_dict = None
        self.name = None

        self.result_summary = None
        self.result_summary_filename = 'IEEE1547-1_summary.csv'
        self.logger = None
        #Postprocessing
        self.pp_ena = self.ts.param_value('IEEE1547dot1.pp_ena')





    '''
    Set functions
    '''

    def set_step_label(self,starting_label=None):
        """
        Write step labels in alphabetical order as shown in the standard
        :param starting_label:
        :return: nothing
        """
        util.set_step_label(self,starting_label=starting_label)

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

    def set_time_settings(self, tr, number_tr):
        self.tr = tr
        self.number_tr = number_tr
        self.logger.set_time_settings(tr, number_tr)

    '''
    Get functions
    '''
    def get_step_label(self):
        label = util.get_step_label(self)
        return label

    def get_script_name(self):
        return self.name

    def get_curve(self):
        """Get curve being tested

        Parameters
        ----------
        curve : int
        """
        return self.curve

    def get_pwr(self):
        """Get curve being tested

        Parameters
        ----------
        curve : float
        """
        return self.pwr
    '''
    Create functions
    '''
    def create_result_summary(self):
        self.result_summary = open(self.ts.result_file_path(self.result_summary_filename), 'a+')
        self.ts.result_file(self.result_summary_filename)

    def create_logger(self):
        """create_logger Create the logger to record all activities and measured
        values from the test

        Parameters
        ----------
        result_summary : [type], optional
            [description], by default None
        """
        self.logger = DataLogging(ts=self.ts, standard_dict=self.standard_dict, support_interfaces={'hil': self.ts.equipments["hil"]})
        self.result_params = self.logger.get_rslt_param_plot()
        if self.result_summary is not None:
            self.result_summary.write(self.logger.get_rslt_sum_col_name())

    def create_dataset_filename(self):
        dataset_filename = self.ts.name.split('.')[0]
        if self.curve is not None:
            dataset_filename += f'_CRV{self.curve}'
        if self.pwr is not None:
            dataset_filename += f'_PWR_{int(self.pwr * 100)}'
        dataset_filename += '.csv'
        return dataset_filename

    '''
    Actions functions
    '''
    def execute_test_procedure_steps(self):
        if self.steps_dict is None:
            raise self.ts.log_error('Steps dictionary is not initialized')

        for step_label, step_dict in self.steps_dict.items():

            if 'V' in step_dict:
                self.ts.log('Voltage step: setting Grid simulator voltage to %s (%s)' % (step_dict['V'], step_label))
                #self.ts.log_debug(50*'=')
                #self.ts.log_debug(f'IMBALANCE ANGLE FIX={self.imbalance_angle_fix}')
                if self.imbalance_angle_fix is None:
                    if self.ts.equipments['grid'] is not None:
                        self.ts.equipments['grid'].voltage(step_dict['V'])
                else:
                    self.ts.log_debug(f'IMBALANCE STEP')
                    if step_dict['V'] in ['case_a', 'case_b']:
                        self.ts.log_debug(f"Applying step {step_dict['V']}")
                        self.set_grid_asymmetric(self.ts.equipments['grid'], step_dict['V'])
                    else:
                        if self.ts.equipments['grid'] is not None:
                            self.ts.equipments['grid'].voltage(step_dict['V'])

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
            if not self.result_summary.closed:
                self.result_summary.write(data)
            else:
                self.result_summary = open(self.ts.result_file_path(self.result_summary_filename), 'a+')
                self.result_summary.write(data)

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
                self.test_name = self.ts.param_value('IEEE1547dot1.test_name')
            self.file_location = self.ts.param_value('IEEE1547dot1.file_location')

        if self.pp_ena == 'Enabled' or self.pp_ena == 'Manual':

            self.ts.log_debug(f'Test Name set to {self.test_name}')
            self.ts.log_debug(f'Postprocessing set at {self.pp_ena}')

            if self.test_name in self.pp_dict:
                # IEEE1547_dict = self.IEEE1547_obj.import_curvepoints(self.test_name)
                self.ts.log_debug('Postprocessing Starting')
                # self.standard_dict from ExtractDatapoints
                IEEE1547pp = IEEE1547postprocessing(self.ts, self.standard_dict)
            else:
                self.ts.log_debug('Postprocessing is not available for this script test')
        elif self.pp_ena == 'Disabled':
            self.ts.log_debug('Postprocessing is disabled')

    def start_recording(self):
        if self.logger is not None and self.ts.slow_functions:
            self.logger.data_capture(True)
        elif not self.ts.slow_functions:
            self.ts.log_debug(f'Waveform should be ARMED in DAQ')
        else:
            self.ts.log_debug(f'Logger is not initiated')

    def stop_recording(self):
        if self.logger is not None:
            self.logger.data_capture(False)
        else:
            self.ts.log_debug(f'Logger is not initiated')

    def save_recording(self):
        if self.logger is not None:
            self.result_params = self.logger.get_rslt_param_plot()
            ds = self.logger.data_capture_dataset()
            self.dataset_filename = self.create_dataset_filename()
            self.ts.log('Saving file: %s' % self.dataset_filename)
            ds.to_csv(self.ts.result_file_path(self.dataset_filename))
            self.result_params['plot.title'] = self.dataset_filename.split('.csv')[0]
            self.ts.result_file(self.dataset_filename, params=self.result_params)
        if self.result_summary is not None:
            self.result_summary.close()
    def close_all_equipments(self):
        """Function to close all equipments if initiated
        """
        super(IEEE1547dot1Layer, self).close_all_equipments()



    '''
    Actions functions
    '''
    def log(self, msg):
        self.ts.log(f'{msg}')

    def log_debug(self, msg):
        self.ts.log_debug(f'{msg}')

if __name__ == "__main__":
    pass
