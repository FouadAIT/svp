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
from datetime import datetime, timedelta
from collections import OrderedDict
import numpy as np
import traceback

from svpelab.Standard_Lib.function_layer import InitializationLayer
from svpelab import das



class DataLogging(InitializationLayer):
#class DataLogging(ExtractDatapoints):

    def __init__(self, ts, standard_dict, support_interfaces=None):
        #super().__init__(ts, standard, test_name)
        self.type_meas = {
            'V': 'AC_VRMS', 
            'I': 'AC_IRMS', 
            'P': 'AC_P', 
            'Q': 'AC_Q', 
            'VA': 'AC_S',
            'F': 'AC_FREQ', 
            'PF': 'AC_PF'
            }
            
        self.display_unit = {
            'V': 'Voltage', 
            'I': 'Current',
            'P': 'Active Power',
            'Q': 'Reactive Power',
            'F': 'Frequency',
            'PF': 'Power Factor'
            }
        self.ts = ts
        self.rslt_sum_col_name = ''
        self.sc_points = {}
        self.tr = None
        self.n_tr = None
        self.initial_value = {}
        self.tr_value = OrderedDict()
        self.current_step_label = None
        self.daq = None
        self.standard_dict = standard_dict
        self.support_interfaces = support_interfaces
        #Settings variable depending on function to be evaluated
        self.x_criteria = self.standard_dict['x_values']
        self.y_criteria = self.standard_dict['y_values']
        self.meas_values = self.standard_dict['measured_values']
        self.set_sc_points()
        if self.ts.slow_functions:
            self.set_result_summary_name()

        else:
            self.ts.log('DAS need to configure Waveform')
        self.set_daq()

        #self.criteria_mode=[False, False, False]

        #Name of file for saved raw data
        self.filename = None

    def set_time_settings(self, tr, number_tr=2):
        self.tr = tr
        self.n_tr = number_tr


    def set_daq(self):
        #self.daq = daq
        self.das_points = self.get_sc_points()
        self.daq = das.das_init(self.ts, sc_points=self.das_points['sc'], support_interfaces=self.support_interfaces)
        if self.daq is not None:
            self.ts.log('DAS: %s' % self.daq)
            self.ts.log('DAS device: %s' % self.daq.info())


    def set_filename(self, filename):
        self.filename = filename

    def close(self):
        if self.daq is not None:
            self.daq.close()
            
    def set_sc_points(self):
        """
        Set SC points for DAS depending on which measured variables initialized and targets

        :return: None
        """
        # TODO : The target value are in percentage (0-100) and something in P.U. (0-1.0)
        #       The measure value are in absolute value
        # TODO : Add an option when self.ts.slow_functions = False. How should it be handle ?

        xs = self.x_criteria
        ys = self.y_criteria
        row_data = []

        for meas_value in self.meas_values:
            row_data.append('%s_MEAS' % meas_value)

        row_data.append('EVENT')
        self.ts.log_debug(f'SC POINTS set at={row_data}')
        self.sc_points['sc'] = row_data

    def get_sc_points(self):
        """
        This getters function returns the sc points for DAS
        :return:            self.sc_points
        """
        return self.sc_points

    def set_result_summary_name(self):
        """
        Write column names for results file depending on which test is being run
        :param nothing:
        :return: nothing
        """
        xs = self.x_criteria
        ys = self.y_criteria
        row_data = []

        for meas_value in self.meas_values:
            row_data.append('%s_MEAS' % meas_value)

            if meas_value in xs:
                row_data.append('%s_TARGET' % meas_value)

        row_data.append('STEP')
        row_data.append('FILENAME')

        self.rslt_sum_col_name = ','.join(row_data) + '\n'

    def get_rslt_param_plot(self):
        """
        This getters function creates and returns all the predefined columns for the plotting process
        :return: result_params
        """
        y_variables = self.y_criteria
        y2_variables = self.x_criteria

        # For VV, VW and FW
        y_points = []
        y2_points = []
        y_title = []
        y2_title = []

        for y in y_variables:
            y_temp = '{}'.format(','.join(str(x) for x in self.get_measurement_label('%s' % y)))
            y_title.append(self.display_unit[y])
            y_points.append(y_temp)
        y_points = ','.join(y_points)
        y_title = ','.join(y_title)

        for y2 in y2_variables:
            y2_temp = '{}'.format(','.join(str(x) for x in self.get_measurement_label('%s' % y2)))
            y2_title.append(self.display_unit[y2])
            y2_points.append(y2_temp)
        y2_points = ','.join(y2_points)
        y2_title = ','.join(y2_title)

        result_params = {
            'plot.title': 'title_name',
            'plot.x.title': 'Time (sec)',
            'plot.x.points': 'TIME',
            'plot.y.points': y_points,
            'plot.y.title': y_title,
            'plot.y2.points': y2_points,
            'plot.y2.title': y2_title,
            'plot.%s_TARGET.min_error' % y: '%s_TARGET_MIN' % y,
            'plot.%s_TARGET.max_error' % y: '%s_TARGET_MAX' % y,
        }

        return result_params

    def get_rslt_sum_col_name(self):
        """
        This getters function returns the column name for result_summary.csv
        :return:            self.rslt_sum_col_name
        """
        return self.rslt_sum_col_name
    
    def data_capture(self, value):
        self.daq.data_capture(value)

    def data_capture_dataset(self):
        return self.daq.data_capture_dataset()

    def write_rslt_sum(self):
        """
        Combines the analysis results, the step label and the filename to return
        a row that will go in result_summary.csv
        :param analysis: Dictionary with all the information for result summary

        :param step:   test procedure step letter or number (e.g "Step G")
        :param filename: the dataset filename use for analysis

        :return: row_data a string with all the information for result_summary.csv
        """

        xs = self.x_criteria
        ys = list(self.y_criteria.keys())
        first_iter = self.tr_value['FIRST_ITER']
        last_iter = self.tr_value['LAST_ITER']
        row_data = []

        # Default measured values are V, P and Q (F can be added) refer to set_meas_variable function
        for meas_value in self.meas_values:
            row_data.append(str(self.tr_value['%s_TR_%d' % (meas_value, last_iter)]))
            # Variables needed for variations
            if meas_value in xs:
                if self.tr_value['%s_TR_TARG_%d' % (meas_value, last_iter)] is None:
                    row_data.append(str(np.NaN))
                else:
                    row_data.append(str(self.tr_value['%s_TR_TARG_%d' % (meas_value, last_iter)]))

        self.ts.log_debug(f'Writing Event into rslt_summary = {self.current_step_label}')
        row_data.append(self.current_step_label)
        row_data.append(str(self.dataset_filename.split('.')[0]))
        # #self.ts.log_debug(f'rowdata={row_data}')
        row_data_str = ','.join(row_data) + '\n'

        return row_data_str

    def record_timeresponse(self, step_dict, step_label = None):
        """
        Get the data from a specific time response (tr) corresponding to x and y values returns a dictionary
        but also writes in the soft channels of the DAQ system
        :param daq:             data acquisition object from svpelab library
        :param initial_value:   the dictionary with the initial values (X, Y and timestamp)
        :param x_target:        The target value of X value (e.g. FW -> f_step)
        :param y_target:        The target value of Y value (e.g. LAP -> act_pwrs_limits)
        :param n_tr:            The number of time responses used to validate the response and steady state values

        :return: returns a dictionary with the timestamp, event and total EUT reactive power
        """

        x = self.x_criteria
        y = list(self.y_criteria.keys())

        self.initial_value['timestamp'] = datetime.now()
        first_tr = datetime.now() + timedelta(seconds=self.tr)

        tr_list = [first_tr]
        self.ts.log_debug(f'TR_LIST={tr_list}')

        self.current_step_label = step_label
        self.daq.sc['event'] = self.current_step_label
        self.ts.log_debug(f'--------------Starting new event {self.current_step_label}------------')

        for i in range(0, self.n_tr+1):
            #self.ts.log_debug(f'I={i}')
            if i != 0:
                tr_list.append(tr_list[i-1] + timedelta(seconds=self.tr))
            for meas_value in self.meas_values:
                #self.ts.log_debug('INIT%s_TR_%s' % (meas_value, i))
                self.tr_value['%s_TR_%s' % (meas_value, i)] = None
                if meas_value in step_dict:
                    #self.ts.log_debug('INIT%s_TR_TARG_%s' % (meas_value, i))
                    self.tr_value['%s_TR_TARG_%s' % (meas_value, i)] = None
                #elif meas_value in y:
                #    self.tr_value['%s_TR_TARG_%s' % (meas_value, i)] = None
        tr_iter = 0
        self.ts.log_debug(f'TR_LIST={tr_list}')

        for tr_ in tr_list:
            now = datetime.now()
            self.daq.sc['EVENT'] = "{0}_TR_{1}".format(self.current_step_label, tr_iter)
            for meas_value in self.meas_values:
                try:
                    #self.ts.log('Value %s: %s' % (meas_value, self.daq.sc['%s_MEAS' % meas_value]))
                    if meas_value in step_dict.keys():
                        self.ts.log_debug(f'STEP_DICT={step_dict[meas_value]}')
                        self.daq.sc['%s_TARGET' % meas_value] = step_dict[meas_value]
                        self.tr_value['%s_TR_TARG_%s' % (meas_value, i)] = step_dict[meas_value]
                except Exception as e:
                    self.ts.log_error('Test script exception: %s' % traceback.format_exc())
                    self.ts.log_debug('Measured value (%s) not recorded: %s' % (meas_value, e))

            if now <= tr_:
                time_to_sleep = tr_ - datetime.now()
                self.ts.log('Waiting %s seconds to get the next Tr data for analysis...' %
                            time_to_sleep.total_seconds())
                self.ts.sleep(time_to_sleep.total_seconds())

            self.ts.log_debug(f'Event={self.daq.sc["EVENT"]}')

            self.tr_value[f'timestamp_{tr_iter}'] = tr_
            self.tr_value['LAST_ITER'] = tr_iter
            tr_iter = tr_iter + 1

        self.tr_value['FIRST_ITER'] = 1

        #return self.tr_value

    def set_filename(self, filename):
        self.dataset_filename = filename

    def get_measurement_label(self, type_meas):
        """
        Returns the measurement label for a measurement type

        :param type_meas:   (str) Either V, P, PF, I, F, VA, or Q
        :return:            (list of str) List of labeled measurements, e.g., ['AC_VRMS_1', 'AC_VRMS_2', 'AC_VRMS_3']
        """
        self.phases = self.ts.param_value('der.phases')

        self.ts.log_debug(f" self.phases  is { self.phases}")
        self.type_meas = {'V': 'AC_VRMS', 'I': 'AC_IRMS', 'P': 'AC_P', 'Q': 'AC_Q', 'VA': 'AC_S',
                            'F': 'AC_FREQ', 'PF': 'AC_PF'}
        meas_root = self.type_meas[type_meas]

        if self.phases == 'Single phase':
            meas_label = [meas_root + '_1']
        elif self.phases == 'Split phase':
            meas_label = [meas_root + '_1', meas_root + '_2']
        elif self.phases == 'Three phase':
            meas_label = [meas_root + '_1', meas_root + '_2', meas_root + '_3']

        return meas_label


    def waveform_capture_dataset(self):
        self.daq.waveform_capture_dataset()