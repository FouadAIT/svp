"""
Copyright (c) 2021, Sandia National Labs, SunSpec Alliance and CanmetENERGY(Natural Resources Canada)
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

import pandas as pd
import os
import inspect
import json
import numpy as np
from svpelab.der import DERError
from svpelab import der
#from svpelab.Standard_Lib.criterias_evaluation import CriteriaEvaluation
from svpelab.Standard_Lib import postprocess_utility
#from tqdm import tqdm
import math
import re

IEEE1547dot1_DEFAULT_ID = 'IEEE1547dot1PP'

IEEE1547dot1_modules = {}


class IEEE1547postprocessing():
    """This driver enable the post processing needed following the UL1741SB standard.
    It contains evaluation of the moving average and the time accuracy testing.
    """

    #def __init__(self, ts, datapoints_dict, working_dir, result_summary=None, time_response=10.0):
    def __init__(self, ts, datapoints_dict, min_max_calculation=True, result_summary='IEEE1547-1_summary.csv'):

        self.group_name = IEEE1547dot1_DEFAULT_ID
        name = lambda name: self.group_name + '.' + name
        self.ts = ts
        self.standard = 'IEEE1547dot1'
        self.result_summary_filename = 'IEEE1547-1_summary.csv'
        self.eut = der.der_init(self.ts)
        if self.eut is None:
            DERError(f'EUT is None')
        self.MRA = {
            'V': 0.01 * self.eut.v_nom(),
            'Q': 0.05 * self.eut.s_rated(),
            'P': 0.05 * self.eut.s_rated(),
            'F': 0.01,
            'T': 0.01,
            'PF': 0.01
        }
        #self.criteria_eval = CriteriaEvaluation(ts, datapoints_dict)
        self.pp_ena = ts.param_value(f'{self.standard}.pp_ena')

        #self.ts.log_debug(f'{self.standard} Post processing set at {self.pp_ena}')

        if self.pp_ena == 'Manual':
            self.test_name = ts.param_value(f'{self.standard}.test_name')
            working_dir = ts.param_value(f'{self.standard}.file_location')
            #self.curve = ts.param_value('UL1741.curve') 
        elif self.pp_ena == 'Enabled':
            working_dir = ts.result_file_path('')

        #self.ts.log_debug(f'workingdir={working_dir}')
        if working_dir[-1] == '\\':
            working_dir = working_dir.rstrip('\\')
        self.working_dir = working_dir

        if result_summary is None:
            self.result_dir = rf'{working_dir}\result_summary.csv'
        else:
            self.result_dir = rf'{working_dir}\{self.result_summary_filename}'

        #self.ts.log_debug(f'working_dir={self.working_dir}')
        #self.ts.log_debug(f'result_dir={self.result_dir}')

        #Meas_value as dict of meas_value
        self.pass_fail_dict = {}
        self.datapoints_dict = datapoints_dict
        #self.y_value_dict = datapoints_dict['y_values']#meas_value_dict

        if len(datapoints_dict['x_values'])==1:
            self.x_datapoints = datapoints_dict['x_values'][0]
        else:
            pass
        self.y_datapoints = []
        if isinstance(datapoints_dict['y_values'], dict):
            #self.ts.log_debug(f'DICT={datapoints_dict["y_values"]}')
            if len(datapoints_dict['y_values'])==1:
                for key, value in datapoints_dict['y_values'].items():
                    self.y_datapoints.append(key)
        else:
            self.y_datapoints.append(datapoints_dict['y_values'][0])


        self.curve = None
        self.cat = 'Category B'

        self.time_accuracy = True
        #Recalculate Target Min Max for result_summary
        self.min_max_calculation = min_max_calculation

        #Initiate PostProcessing
        self.ts.log_debug(f'Starting {self.standard} Post Processing')
        self.start()
        self.rearrange_columns_order()
        self.to_csv(self.ts.result_file_path('IEEE1547-1_summary.csv'))

    def set_curve(self, curve):
        self.curve = curve

    def set_category(self, category):
        self.cat = category

    def start(self):
        self.files_df = {}
        #self.ts.log_debug(f'working_dir={self.working_dir}')
        #self.ts.log_debug(f'result_dir={self.result_dir}')

        #Load csv files as Dataframes
        #Load result summary file
        self.rs_df = pd.read_csv(self.result_dir)

        #Return all filenames present in result_summary
        self.rs_df.rename(columns=lambda x: x.strip(), inplace=True)

        self.filenames = self.get_filenames(self.rs_df)
        self.ts.log_debug(f'Filenames presents ={self.filenames}')
        self.ts.log_debug(f'result_summary={self.rs_df.head()}')

        #Load raw data file and aggregate values correctly for measured values
        self.aggregate_measured_values()



        for meas_value in self.x_datapoints:

            #if self.validate_cols_df(self.rs_df, f'{meas_value}_MEAS'):
            self.pass_fail_dict[f'{meas_value}_MEAS'] = []

        for meas_value in self.y_datapoints:
            #self.ts.log_debug(f'meas_value={meas_value}')
            self.pass_fail_dict[f'{meas_value}_MEAS'] = []
            if self.min_max_calculation:
                self.pass_fail_dict[f'{meas_value}_TARGET'] = []
                self.pass_fail_dict[f'{meas_value}_TARGET_MIN'] = []
                self.pass_fail_dict[f'{meas_value}_TARGET_MAX'] = []
                self.pass_fail_dict[f'{meas_value}_TR_WITHIN_BOUNDS_BY_TR=1_PASSFAIL'] = []
                self.pass_fail_dict[f'{meas_value}_TR_WITHIN_BOUNDS_BY_TR=4_PASSFAIL'] = []
            if self.time_accuracy:
                self.pass_fail_dict[f'{meas_value}_TR_90PCT_BY_TR=1_PASSFAIL'] = []



        self.process_data()

    def validate_cols_df(self, df, cols):
        """[summary]

        Parameters
        ----------
        df : [type]
            [description]
        cols : [type]
            [description]

        Returns
        -------
        [type]
            [description]
        """
        if df[cols].isnull().values().any():
            return True
        else:
            return False


    def aggregate_measured_values(self):
        """This function will aggregate all the measured values fixed following the json formatted curve files
        """
        for filename in self.filenames:
            complete_filename = f'{self.working_dir}\\{filename}.csv'
            self.files_df[filename] = pd.read_csv(complete_filename)
            self.files_df[filename] = self.files_df[filename].rename(columns=lambda x: x.strip().upper())

            df_obj = self.files_df[filename].select_dtypes(['object'])
            self.files_df[filename][df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
            for meas_values in self.datapoints_dict['measured_values']:
                self.files_df[filename] = postprocess_utility.aggregate_meas(ts=self.ts, df=self.files_df[filename], type_meas=meas_values)

            self.files_df[filename].to_csv(self.ts.result_file_path(f'{filename}.csv'),index=False)

    def get_filenames(self, df):
        """get_filenames Function to extract all filenames included in the result summary

        Parameters
        ----------
        df : Dataframe
            Pandas Dataframe containing a column 'FILENAME'

        Returns
        -------
        List of strings
            List containing Filename under string format
        """
        ##self.ts.log_debug(f'DF={df.head()}')
        return df['FILENAME'].unique()

    def process_data(self):
        """This function will serve as the main core function where all the processing will
        be done on the dataframe
        """
        tr1df = {} # Dataframe related to the dynamic time response value
        tr4df = {} # Dataframe related to the steady-state time response value
        for index, row in self.rs_df.iterrows(): #  For loop parsing though the result summary dataframe (self.rs_df)
            self.current_step = row['STEP'] # Represents the current step analysed (ex.: STEP G)
            # TODO : Throw a value error when tr1df or tr1df is empty. You cannot process if missing these dictionnaries

            tr1df[row['FILENAME']] = self.x_tr_first(df=self.files_df[row['FILENAME']], step=row['STEP'], x=1) # Search for the first value at the dynamic time response (event TR_1) at the current step (ex: first STEP G_TR_1 of EVENT column of the results csv files)
            tr4df[row['FILENAME']] = self.x_tr_first(df=self.files_df[row['FILENAME']], step=row['STEP'], x=4) # Same as above, but at the steady-state time response (event TR_4) (ex: first STEP G_TR_4)

            self.curve = re.search('(?<=_CRV)[0-9]+', row['FILENAME']).group() # find the curve number applied with a regex function
            self.ts.log_debug(f"Filename : {row['FILENAME']} use curve {self.curve}") # Logging the file name of the csv file and the curve number of the GSF (Grid Support Function)
            for meas_x_value in self.x_datapoints: # For loop on the measured x values (ex: 'V' for VW)
                for meas_y_value in self.y_datapoints: # For loop on the measured y values (ex: 'P' for VW)
                    #If there was no TR1 in the dataframe output
                    if tr4df[row['FILENAME']].empty or tr1df[row['FILENAME']].empty: # If the value at steady-state or dynamic time-response doesn't exist, replace the values by nan values
                        self.pass_fail_dict[f'{meas_x_value}_MEAS'].append(np.nan)
                        self.pass_fail_dict[f'{meas_y_value}_MEAS'].append(np.nan)
                        if self.min_max_calculation:
                            self.pass_fail_dict[f'{meas_y_value}_TARGET'].append(np.nan)
                            self.pass_fail_dict[f'{meas_y_value}_TARGET_MIN'].append(np.nan)
                            self.pass_fail_dict[f'{meas_y_value}_TARGET_MAX'].append(np.nan)
                            self.pass_fail_dict[f'{meas_y_value}_TR_WITHIN_BOUNDS_BY_TR=1_PASSFAIL'].append(np.nan)
                            self.pass_fail_dict[f'{meas_y_value}_TR_WITHIN_BOUNDS_BY_TR=4_PASSFAIL'].append(np.nan)
                        if self.time_accuracy:
                            self.pass_fail_dict[f'{meas_y_value}_TR_90PCT_BY_TR=1_PASSFAIL'].append(np.nan)

                    else: # If the value at steady-state or dynamic time-response exist, evaluate the different criterias related to the y values
                        self.x = meas_x_value # set the current x value attribute
                        self.y = meas_y_value # set the current y value attribute
                        self.pass_fail_dict[f'{meas_x_value}_MEAS'].append(tr4df[row['FILENAME']][f'{meas_x_value}_MEAS'].iloc[0])  # add the x measured value at steady-state time response to the pass/fail dict
                        self.pass_fail_dict[f'{meas_y_value}_MEAS'].append(tr4df[row['FILENAME']][f'{meas_y_value}_MEAS'].iloc[0]) # add the y measured value at steady-state time response to the pass/fail dict
                        self.tr = self.datapoints_dict['Category B'][f'curve{self.curve}']['TR'] # find the Time-response written in the GSF json file (See CurvePoints folder)
                        self.ts.log_debug(f"self.pass_fail_dict = {self.pass_fail_dict}") # log pass/fail dict in the svp run window
                        self.y_targ_min, self.y_targ_max, self.y_targ = self.eval_min_max(tr4df[row['FILENAME']][f'{meas_x_value}_MEAS'].iloc[0])  # Determine the target values depending on the GSF curve and current x measured value (Look into eval_min_max and interpolate_value of _criterias_evaluation.py for details)
                        self.pass_fail_dict[f'{meas_y_value}_TR_WITHIN_BOUNDS_BY_TR=1_PASSFAIL'].append(self.verify_passfail(df=tr1df[row['FILENAME']], key=meas_y_value)) # (min/max criteria) Verifies if the measured y value at dynamic time response is between the minimum and maximum target value
                        self.pass_fail_dict[f'{meas_y_value}_TR_WITHIN_BOUNDS_BY_TR=4_PASSFAIL'].append(self.verify_passfail(df=tr4df[row['FILENAME']], key=meas_y_value)) # (min/max criteria) Verifies if the measured y value at steady-state time response is between the minimum and maximum target value
                        # TODO : Changer le nom pour le standard open_loop_resp_criteria
                        tr_90PCT_by_tr1_pf = self.time_accuracy_eval(self.files_df[row['FILENAME']], tr1df[row['FILENAME']]['TIME'], key=meas_y_value) # (Dynamic criteria) Verifies if the open loop time response criteria of IEEE1547 standard pass or fail for the y measured value at dynamic time response
                        if tr_90PCT_by_tr1_pf is None : # Verifies if the dynamic pass/fail was done correctly
                            raise ValueError(f"Something is wrong with the 90pc of TR=1 passfail criteria ...  Passfail result is empty")
                        if self.min_max_calculation: # If min/max criteria evaluated, then add the related values to the pass/fail dict
                            self.pass_fail_dict[f'{meas_y_value}_TARGET'].append(self.y_targ )
                            self.pass_fail_dict[f'{meas_y_value}_TARGET_MIN'].append(self.y_targ_min)
                            self.pass_fail_dict[f'{meas_y_value}_TARGET_MAX'].append(self.y_targ_max)
                        if self.time_accuracy: # If dynamic criteria evaluated, then add the related values to the pass/fail dict
                            self.pass_fail_dict[f'{meas_y_value}_TR_90PCT_BY_TR=1_PASSFAIL'].append(tr_90PCT_by_tr1_pf)

        # Rewrite the result summary dataframe filled with None values with the data in the pass/fail dict
        for key, list_value in self.pass_fail_dict.items():
            if 'PASSFAIL' in key or 'LIST' in key:
                serie = pd.Series(self.pass_fail_dict[key], index=self.rs_df.index, dtype='string')
                self.rs_df[key] = serie
            else:
                self.ts.log_debug(f"self.pass_fail_dict[key] {self.pass_fail_dict[key]}")
                serie = pd.Series(self.pass_fail_dict[key], index=self.rs_df.index, dtype='float64')
                self.rs_df[key] = serie
        # When the result summary dataframe is done being rewritten it is reconverted in a csv file overwriting the previous one (see the end of the _init_ of the PostProcess class)



    def to_csv(self, filename):
        """This function will convert the dataframe into a csv formatted file.

        Parameters
        ----------
        filename : string
            desired name of the ouputted csv file
        """
        self.rs_df.to_csv(filename, index=False)
    
    def rearrange_columns_order(self, criteria_mode=[0,0,0]):
        """rearrange_columns_order 
        This function will rearrange the order displayed into the dataframe

        Parameters
        ----------
        criteria_mode : list, optional
            This list must be a list of 3 booleans to indicate which criterias 
            validation has been done, by default [1,1,1]
        """
        xs = self.datapoints_dict['x_values']
        ys = self.datapoints_dict['y_values']
        meas_values = self.datapoints_dict['measured_values']
        
        row_data = []
        for meas_value in meas_values:
            if '%s_MEAS' % meas_value in self.rs_df.columns:
                row_data.append('%s_MEAS' % meas_value)

            if meas_value in xs:
                row_data.append('%s_TARGET' % meas_value)

            elif meas_value in ys:
                if self.min_max_calculation:
                    row_data.append('%s_TARGET_MIN' % meas_value)
                    row_data.append('%s_TARGET' % meas_value)
                    row_data.append('%s_TARGET_MAX' % meas_value)
                    row_data.append(f'{meas_value}_TR_WITHIN_BOUNDS_BY_TR=1_PASSFAIL')
                    row_data.append(f'{meas_value}_TR_WITHIN_BOUNDS_BY_TR=4_PASSFAIL')

                if self.time_accuracy:
                    row_data.append(f'{meas_value}_TR_90PCT_BY_TR=1_PASSFAIL')


        row_data.append('STEP')
        row_data.append('FILENAME')

        #self.ts.log_debug(f'ORDER={row_data}')
        self.rs_df= self.rs_df[row_data]
        #self.ts.log_debug(f'rearrange_columns_order of  self.rs_df={ self.rs_df.head(5)}')


    def step_df(self, df, step, col='EVENT'):
        """This function will return a dataframe matching the matching step event

        Parameters
        ----------
        df : Pandas.Dataframe
            This should be the dataframe containing the values needed for the calculation
        step : str
            step is the string variable indicating which step event this is. 
            (e.g: STEP A, STEP B, etc.)
        col : str, optional
            col is the string variable indicating the column name from the dataframe 
            where we will extract the step value from the dataframe, by default 'EVENT'

        Returns
        -------
        Pandas.Series
            This function will return a dataframe matching the matching step event
        """
        step_df = df[df[col].str.contains(f'{step}_TR_[1-4]', regex=True)].mean()
        #step_df = df[df[col].str.contains(f'{step}_TR_{tr}', regex=True)].mean()

        return step_df

    def x_tr_first(self, df, step, col='EVENT', x=1):
        """This function will return the first value TR of a step

        Parameters
        ----------
        df : Pandas.Dataframe
            This should be the dataframe containing the values needed.
        step : str
            step is the string variable indicating which step event this is. 
            (e.g: STEP A, STEP B, etc.)
        col : str, optional
            col is the string variable indicating the column name from the dataframe 
            where we will extract the step value from the dataframe, by default 'EVENT'
        x : int
            x represent which step is needed. Values ranging from [0-4]

        Returns
        -------
        Pandas.Dataframe
            Returns the dataframe containing the first tr row of a desired step
        """
        trXdf = df.loc[(df[col] == f'{step}_TR_{x}')]
        trXdf_first = trXdf[trXdf['TIME'] == trXdf['TIME'].min()]

        return trXdf_first

    def time_accuracy_eval(self, df, tr, key, accuracy=0.01):
        """time_accuracy_eval This function evaluates the time accuracy after the first TR
        It will be TR1 +- desired accuracy% and will evaluate if both values are within the
        desired target

        Parameters
        ----------
        df : Pandas.Dataframe
            This should be the dataframe containing the values needed.
        tr : Pandas.Series
            Series containing the exact timestamp
        accuracy : float, optional
            percentage of the time, by default 0.05

        Returns
        -------
        Pandas.Dataframe
            Two dataframes containing both minimum value and maximum value of the resulting time + accuracy
        """
        column_name = f'{key}_MEAS'
        t_mra = accuracy*self.tr*1.5
        if t_mra < 0.05:
            t_mra = 0.05
        exact_time = tr.values[0]
        """
         TRANSIENT: Open Loop Time Response (OLTR) = 90% of (y_tr_4-y_tr_0) + y_tr_0

            The variable y_tr is the value used to verify the time response requirement.
            |----------|----------|----------|----------|
                     1st tr     2nd tr     3rd tr     4th tr
            |          |                                | 
            y_tr_0    y_tr_1                          y_tr_4

            (1547.1)After each step, the open loop response time, Tr, is evaluated.
            The expected output, Y(Tr), at one times the open loop response time,
            is calculated as 90%*(y_tr_4- y_tr_0 ) + y_tr_0
        """


        y_tr_0_df = self.x_tr_first(df, self.current_step, x=0)[["TIME",column_name]]
        y_tr_0_value = y_tr_0_df[column_name].values[0]
        tr_0_value = y_tr_0_df["TIME"].values[0]

        y_tr_1_df = self.x_tr_first(df, self.current_step, x=1)[["TIME",column_name]]
        y_tr_1_value = y_tr_1_df[column_name].values[0]
        tr_1_value = y_tr_1_df["TIME"].values[0]

        y_tr_4_df = self.x_tr_first(df, self.current_step, x=4)[["TIME",column_name]]
        y_tr_4_value = y_tr_4_df[column_name].values[0]
        tr_4_value = y_tr_4_df["TIME"].values[0]

        y_ss = self.y_targ

        duration = tr_1_value- tr_0_value

        y_target = self.calculate_open_loop_value(y_tr_0=y_tr_0_value,
                                                  y_ss=y_ss,
                                                  duration=duration,
                                                  tr=self.tr)



        if y_tr_0_value <= y_target:  # increasing values of y
            increasing = True
            # Y(time) = open loop curve, so locate the Y(time) value on the curve
            y_min = self.calculate_open_loop_value(y_tr_0=y_tr_0_value,
                                                   y_ss=y_ss,
                                                   duration=duration - 1.5 * t_mra,
                                                   tr=self.tr)
            # Determine maximum value based on the open loop response expectation
            y_max = self.calculate_open_loop_value(y_tr_0=y_tr_0_value,
                                                   y_ss=y_ss,
                                                   duration=duration + 1.5 * t_mra,
                                                   tr=self.tr)
        else:  # decreasing values of y
            increasing = False
            # Y(time) = open loop curve, so locate the Y(time) value on the curve
            y_min = self.calculate_open_loop_value(y_tr_0=y_tr_0_value,
                                                   y_ss=y_ss,
                                                   duration=duration + 1.5 * t_mra,
                                                   tr=self.tr)
            # Determine maximum value based on the open loop response expectation
            y_max = self.calculate_open_loop_value(y_tr_0=y_tr_0_value,
                                                   y_ss=y_ss,
                                                   duration=duration - 1.5 * t_mra,
                                                   tr=self.tr)
        y_min -= 1.5 * self.MRA[key]
        y_max += 1.5 * self.MRA[key]
        passfail = None
        if y_min <= y_tr_1_value <= y_max:
             passfail = 'Pass'
        else:
            passfail = 'Fail'
        return passfail

    def calculate_open_loop_value(self, y_tr_0, y_ss, duration, tr):
        """
        Calculated the anticipated Y(Tr +/- MRA_T) values based on duration and Tr

        Note: for a unit step response Y(t) = 1 - exp(-t/tau) where tau is the time constant

        :param y_tr_0: initial Y(0) value
        :param y_ss: steady-state solution or the target value, e.g., Y(infinity)
        :param duration: time since the change in the input parameter that the output should be calculated
        :param tr: open loop response time (90% change or 2.3 * time constant)

        :return: output Y(duration) anticipated based on the open loop response function
        """

        time_const = tr / (-(math.log(0.1)))  # ~2.3 * time constants to reach the open loop response time in seconds
        number_of_taus = duration / time_const  # number of time constants into the response
        resp_fraction = 1 - math.exp(-number_of_taus)  # fractional response after the duration, e.g. 90%

        # Y must be 90% * (Y_final - Y_initial) + Y_initial
        resp = (y_ss - y_tr_0) * resp_fraction + y_tr_0  # expand to y units

        return resp

    def time_accuracy_eval_UL1741(self, df, tr, key, accuracy=0.01):
        """time_accuracy_eval This function evaluates the time accuracy after the first TR
        It will be TR1 +- desired accuracy% and will evaluate if both values are within the
        desired target

        Parameters
        ----------
        df : Pandas.Dataframe
            This should be the dataframe containing the values needed.
        tr : Pandas.Series
            Series containing the exact timestamp
        accuracy : float, optional
            percentage of the time, by default 0.05

        Returns
        -------
        Pandas.Dataframe
            Two dataframes containing both minimum value and maximum value of the resulting time + accuracy
        """
        column_name = f'{key}_MEAS'
        t_mra = accuracy*self.tr*1.5
        if t_mra < 0.05:
            t_mra = 0.05
        exact_time = tr.values[0]

        new_df = df.loc[(df['TIME']>=(exact_time - t_mra)) & (df['TIME']<=(exact_time + t_mra))]
        #self.ts.log_debug(f'NEW_DF={new_df[column_name].head()}')

        y_ini = self.x_tr_first(df, self.current_step, x=0)[column_name].min()
        y_final = self.x_tr_first(df, self.current_step, x=4)[column_name].min()
        #self.ts.log_debug(f'y_ini={y_ini}')
        #self.ts.log_debug(f'y_final={y_final}')
        upper_value = y_ini + 0.9*(y_final - y_ini) + 1.5*self.MRA[key]
        lower_value = y_ini + 0.9*(y_final - y_ini) - 1.5*self.MRA[key]
        #self.ts.log_debug(f'Upper_bound_target={upper_value}')
        #self.ts.log_debug(f'Lower_bound_target={lower_value}')

        new_df['Within_bounds'] = np.where((lower_value<=new_df[column_name]) \
            & (upper_value>=new_df[column_name]), True, False)

        #self.ts.log_debug(new_df['Within_bounds'].head())
        if new_df['Within_bounds'].eq(True).all():
            return 'Pass', lower_value, upper_value, new_df[column_name].values.tolist()
        else:
            return 'Fail', lower_value, upper_value, new_df[column_name].values.tolist()

        #return new_df

    def verify_passfail(self, df, key, column_name=None):
        """This function verifies if the value is within the minimum and the maximum.
        It allows the function to generate a pass-fail after the validation.

        Parameters
        ----------
        df : Pandas.Dataframe
            This should be the dataframe containing the values needed.
        key : str
            This should be a key representing the desired measured type of values such
            as V, P, Q, F or I depending on what's needed.
        column_name : str
            This should be a key representing the desired column name to be evaluated. 
            If it is not inputted, it will be defaulted to None and will be the same as key value.

        Returns
        -------
        str
            returns a string containing either a pass or fail.
        """
        if column_name is None:
            column_name = f'{key}_MEAS'

        if column_name not in df.columns:
            raise KeyError(f'{column_name} not in dataframe')

        if self.min_max_calculation:
            #self.ts.log_debug(f'Targ_min={self.y_targ_min}')
            #self.ts.log_debug(f'Targ_max={self.y_targ_max}')
            #self.ts.log_debug(f'V_TOCHECK={df[column_name].iloc[0]}')
            if self.y_targ_min <= df[column_name].iloc[0] and self.y_targ_max >= df[column_name].iloc[0]:
                #self.ts.log_debug(f'RESULT=PASS')
                return 'Pass'
            else:
                #self.ts.log_debug(f'RESULT=FAIL')

                return 'Fail'            
        else:
            ##self.ts.log_debug(f'COLUMNS={df.columns}')
            if f'{key}_TARGET_MIN' not in df.columns:
                raise KeyError(f'{key}_TARGET_MIN not in dataframe')
            elif f'{key}_TARGET_MAX' not in df.columns:
                raise KeyError(f'{key}_TARGET_MAX not in dataframe')

            if df[f'{key}_TARGET_MIN'].iloc[0] <= df[column_name].iloc[0] and df[f'{key}_TARGET_MAX'].iloc[0] >= \
                    df[column_name].iloc[0]:
                return 'Pass'
            else:
                return 'Fail'

    #Import missing evaluate criterias functions     
    from svpelab.Standard_Lib._criterias_evaluation import eval_min_max, interpolate_value, reference_unit
