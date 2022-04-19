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
import collections 
import numpy as np
import pandas as pd
import random

from svpelab.Standard_Lib.IEEE1547.IEEE1547_layer import IEEE1547dot1Layer

LFRT = "LFRT"
HFRT = "HFRT"
LV = 'LV'
HV = 'HV'
CAT_2 = 'CAT_2'
CAT_3 = 'CAT_3'

class VoltageRideThrough(IEEE1547dot1Layer):

    #def __init__(self, ts, function='Volt-Watt', standard='IEEE1547dot1', imbalance_angle_fix=None):
    def __init__(self, ts, function='Volt-Watt', imbalance_angle_fix=None):
        super().__init__(ts, function, imbalance_angle_fix=imbalance_angle_fix)

        #self.ts = ts
        self.name = 'Voltage Ride-Through'
        #self.ts.log_debug(f'Imbalance Fix VW lib= {imbalance_angle_fix}')
        self.wfm_header = None
        self.phase_combination = None
        self.params = {}
        self.ts.slow_functions = False

    def set_vrt_params(self):
        try:
            # RT test parameters
            self.params["lv_mode"] = self.ts.param_value('vrt.lv_ena')
            self.params["hv_mode"] = self.ts.param_value('vrt.hv_ena')
            self.params["categories"] = self.ts.param_value('vrt.cat')
            self.params["range_steps"] = self.ts.param_value('vrt.range_steps')
            self.params["eut_startup_time"] = float(self.ts.param_value('der.startup_time'))
            #self.params["model_name"] = self.hil.rt_lab_model
            self.params["range_steps"] = self.ts.param_value('vrt.range_steps')
            self.params["phase_comb"] = self.ts.param_value('vrt.phase_comb')
            self.params["dataset"] = self.ts.param_value('vrt.dataset_type')
            self.params["consecutive_ena"] = self.ts.param_value('vrt.consecutive_ena')

        except Exception as e:
            self.ts.log_error('Incorrect Parameter value : %s' % e)
            raise

    def set_vrt_modes(self):
        modes = []
        lv_mode = True if self.params["lv_mode"] == 'Enabled' else print("")
        hv_mode = True if self.params["hv_mode"] == 'Enabled' else print("")
        cat2_enabled = True if (self.params["categories"] == CAT_2 or self.params["categories"] == 'Both') else print("")
        cat3_enabled = True if (self.params["categories"] == CAT_3 or self.params["categories"] == 'Both') else print("")

        if lv_mode and cat2_enabled:
            modes.append(f"{LV}_{CAT_2}")
        if lv_mode and cat3_enabled:
            modes.append(f"{LV}_{CAT_3}")
        if hv_mode and cat2_enabled:
            modes.append(f"{HV}_{CAT_2}")
        if hv_mode and cat3_enabled:
            modes.append(f"{HV}_{CAT_3}")
        self.params["modes"] = modes

    def set_wfm_file_header(self):
        self.wfm_header = ['TIME',
                           'AC_V_1', 'AC_V_2', 'AC_V_3',
                           'AC_I_1', 'AC_I_2', 'AC_I_3',
                           'AC_FREQ_CMD', "TRIGGER"]

    def set_result_summary_name(self):
        row_data = []
        row_data.append('MODE TESTED')
        if self.wav_ena :
            row_data.append('WAVEFORM FILE')
        if self.data_ena :
            row_data.append('DATA FILE')
        self.rslt_sum_col_name = ','.join(row_data) + '\n'


    def get_vrt_stop_time(self, test_sequences_df):
        return test_sequences_df["VRT_END_TIMING"].iloc[-1]

    def get_wfm_file_header(self):
        return self.wfm_header

    def get_modes(self):
        return self.params["modes"]

    def create_configuration_variables(self):
        self.set_vrt_params()
        self.set_vrt_modes()
        self.set_wfm_file_header()


        phase_comb_list = []

        if self.ts.param_value('vrt.one_phase_mode') == "Enabled":
            phase_comb_list.append([self.ts.param_value('vrt.one_phase_value')])

        if self.ts.param_value('vrt.two_phase_mode') == "Enabled":
            phase_comb_list.append([self.ts.param_value('vrt.two_phase_value_1'), self.ts.param_value('vrt.two_phase_value_2')])

        if self.ts.param_value('vrt.three_phase_mode') == "Enabled":
            phase_comb_list.append(['A', 'B', 'C'])

        low_pwr_ena = self.ts.param_value('vrt.low_pwr_ena')
        high_pwr_ena = self.ts.param_value('vrt.high_pwr_ena')
        low_pwr_value = self.ts.param_value('vrt.low_pwr_value')
        high_pwr_value = self.ts.param_value('vrt.high_pwr_value')

        pwr_lvl = []

        if low_pwr_ena == 'Enabled':
            pwr_lvl.append(low_pwr_value)
        else:
            self.ts.log_debug('No low power chosen')
        if high_pwr_ena == 'Enabled':
            pwr_lvl.append(high_pwr_value)
        else:
            self.ts.log_debug('No high power chosen')
        if high_pwr_ena == 'Disabled' and low_pwr_ena == 'Disabled':
            self.ts.log_error('No power tests included in VRT test!')

        loops = []
        for current_mode in self.get_modes():
            for pwr in pwr_lvl:
                for phase in phase_comb_list :
                    loops.append({"MODE": current_mode,
                                  "PWR": pwr,
                                  "PHASE": phase})
        return loops

    def set_test_bench_equipment(self):
        self.set_grid_to_nominal()

        self.set_dc_pwr(irr=1100, pwr=self.get_pwr())

        self.vrt_config_to_eut()

    def set_loop_test_procedure_configuration(self, loop_configuration):
        #self.set_curve(int(re.search('(?<=CRV)[0-9]+', loop).group()))
        self.loop_configuration = loop_configuration

        self.set_pwr_setting(pwr=self.loop_configuration["PWR"])
        #self.set_time_settings(tr=self.vw_response_time[self.get_curve()], number_tr=4)
        self.dataset_filename = f'{self.loop_configuration["MODE"]}_{round(self.get_pwr() * 100)}PCT_{"".join(self.loop_configuration["PHASE"])}'




    def set_phase_combination(self):
        parameters = []
        phase = self.loop_configuration["PHASE"]
        self.ts.log_debug(f"set_phase_combination : {phase}")
        for ph in phase:
            parameters.append((f"VRT_PH{ph}_ENABLE", 1.0))
        self.set_parameters_on_hil(parameters)
    def set_vrt_model_parameters(self, test_sequence):
        parameters = []
        # if "A" in phase_combination_label:
        #     parameters.append(("VRT_PHA_ENABLE", 1.0))
        # if "B" in phase_combination_label:
        #     parameters.append(("VRT_PHB_ENABLE", 1.0))
        # if "C" in phase_combination_label:
        #     parameters.append(("VRT_PHC_ENABLE", 1.0))

        # Enable VRT mode in the IEEE1547_fast_functions model
        parameters.append(("MODE", 3.0))

        vrt_condition_list = self.extend_list_end(test_sequence["VRT_CONDITION"].to_list(), 0.0, 20)
        parameters.append(("VRT_CONDITION", vrt_condition_list))

        vrt_start_timing_list = self.extend_list_end(test_sequence["VRT_START_TIMING"].to_list(), 0.0, 20)
        parameters.append(("VRT_START_TIMING", vrt_start_timing_list))

        vrt_end_timing_list = self.extend_list_end(test_sequence["VRT_END_TIMING"].to_list(), 0.0, 20)
        parameters.append(("VRT_END_TIMING", vrt_end_timing_list))

        vrt_values_list = self.extend_list_end(test_sequence["VRT_VALUES"].to_list(), 0.0, 20)
        parameters.append(("VRT_VALUES", vrt_values_list))
        self.set_parameters_on_hil(parameters)

    def extend_list_end(self, _list, extend_value, final_length):
        list_length = len(_list)
        _list.extend([float(extend_value)] * (final_length - list_length))
        return _list
    def create_dict_steps(self):
        """
        This function creates the dictionary steps for Volt-Watt
        :param mode (string): Verifies if VW is operating under normal or imbalanced grid mode
        :return: vw_dict_steps (dictionary)
        """
        pass

    def save_recording(self):
        self.ts.log('Processing waveform dataset(s)')
        wave_start_filename = self.dataset_filename + "_WAV.csv"
        ds = self.logger.waveform_capture_dataset()  # returns list of databases of waveforms (overloaded)
        if ds is not None:
            self.ts.log(f'Number of waveforms to save {len(ds)}')
            if len(ds) > 0:
                ds[0].to_csv(self.ts.result_file_path(wave_start_filename))
                self.ts.result_file(wave_start_filename)


    def vrt_config_to_eut(self):
            # TODO : Add the VRT Configuration to EUT
            pass

    def vv_config_to_eut(self):
            # TODO : Add the VV Configuration to EUT
            pass

    def get_test_sequence(self, current_mode, test_condition):
        index = ['VRT_CONDITION', 'MIN_DURATION', 'VRT_VALUES']
        T0 = self.params["eut_startup_time"]
        if self.params["consecutive_ena"] == "Enabled":
            CONSECUTIVE = True
        else:
            CONSECUTIVE = False
        test_sequences_df = pd.DataFrame(columns=index)
        if CAT_2 in current_mode and LV in current_mode:
            if CONSECUTIVE:
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                # ABCDEF
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)
                # ABCD'F
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)

            else:
                # ABCDEF
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["F"], ignore_index=True)
        elif CAT_3 in current_mode and LV in current_mode:
            if CONSECUTIVE:
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                # ABC'DE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
            else:
                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
        elif CAT_2 in current_mode and HV in current_mode:
            if CONSECUTIVE:
                # ABCD
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)

                # ABCDE
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
            else:
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["D"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["E"], ignore_index=True)
                pass
        elif CAT_3 in current_mode and HV in current_mode:
            if CONSECUTIVE:
                # AB
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)

                # AB
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)

                # ABC
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)

                # AB'C
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B'"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
            else:
                test_sequences_df = test_sequences_df.append(test_condition["A"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["B"], ignore_index=True)
                test_sequences_df = test_sequences_df.append(test_condition["C"], ignore_index=True)
                pass

        test_sequences_df.loc[0, 'VRT_START_TIMING'] = T0
        # Calculate the timing sequences
        test_sequences_df.loc[0, 'VRT_END_TIMING'] = T0 + test_sequences_df.loc[0, 'MIN_DURATION']
        for i in range(1, len(test_sequences_df)):
            test_sequences_df.loc[i, 'VRT_START_TIMING'] = test_sequences_df.loc[i - 1, 'VRT_END_TIMING']
            test_sequences_df.loc[i, 'VRT_END_TIMING'] = test_sequences_df.loc[i, 'VRT_START_TIMING'] + \
                                                         test_sequences_df.loc[i, 'MIN_DURATION']
        self.ts.log_debug(test_sequences_df)

        return test_sequences_df

    def execute_test_procedure_steps(self):
        self.logger.set_filename(self.dataset_filename)
        if self.result_summary.closed:
            self.result_summary = open(self.ts.result_file_path(self.result_summary_filename), 'a+')
        self.result_summary.write('Test Name, Waveform File, RMS File\n')
        self.ts.log_debug(f'Setting power level to {self.get_pwr()}')

        self.vrt_test_sequences = self.set_test_conditions()
        self.set_phase_combination()
        vrt_stop_time = self.get_vrt_stop_time(self.vrt_test_sequences)
        vrt_stop_time = vrt_stop_time + 5
        # self.ts.log('Stop time set to %s' % phil.set_stop_time(vrt_stop_time))
        self.set_vrt_model_parameters(self.vrt_test_sequences)

        self.vrt_config_to_eut()
        self.vv_config_to_eut()

        self.chil_start_simulation()
        sim_time = self.get_chil_time()
        while (vrt_stop_time - sim_time) > 1.0:  # final sleep will get to stop_time.
            sim_time = self.get_chil_time()
            self.ts.log('Sim Time: %0.3f.  Waiting another %0.3f sec before saving data.' % (
                sim_time, vrt_stop_time - sim_time))
            self.ts.sleep(5)

    def set_test_conditions(self):
        current_mode = self.loop_configuration["MODE"]
        # Set useful variables
        mra_v_pu = self.MRA["V"] / self.v_nom
        RANGE_STEPS = self.params["range_steps"]
        index = ['VRT_CONDITION', 'MIN_DURATION', 'VRT_VALUES']
        TEST_CONDITION = {}
        # each condition are set with a pandas series as follow:
        # pd.Series([test condition, minimum duration(s), Residual Voltage (p.u.)], index=index)

        # TABLE 4 - CATEGORY II LVRT TEST CONDITION
        if CAT_2 in current_mode and LV in current_mode:
            # The possible test conditions are ABCDD'EF
            if RANGE_STEPS == "Figure":
                # Using value of Figure 2 - CATEGORY II LVRT test signal
                TEST_CONDITION["A"] = pd.Series([1, 10, 0.94], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.160, 0.3 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.160, 0.45 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 2.68, 0.65], index=index)
                TEST_CONDITION["D'"] = pd.Series([4 + 10, 7.68, 0.67 + 2 * mra_v_pu], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 2.0, 0.88], index=index)
                TEST_CONDITION["F"] = pd.Series([6, 120.0, 0.94], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 10, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.160, random.uniform(0.0, 0.3 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.160, random.uniform(0.0, 0.45 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 2.68, random.uniform(0.45 + 2 * mra_v_pu, 0.65 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["D'"] = pd.Series([4 + 10, 7.68, random.uniform(0.67, 0.88 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 2.0, random.uniform(0.65 + 2 * mra_v_pu, 0.88 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["F"] = pd.Series([6, 120.0, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)

        # TABLE 5 - CATEGORY III LVRT TEST CONDITION
        elif CAT_3 in current_mode and LV in current_mode:
            # The possible test conditions are ABCC'DE
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 5, 0.94], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 1, 0.05 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 9, 0.5 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C'"] = pd.Series([3 + 10, 9, 0.52 + 2 * mra_v_pu], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 10.0, 0.7], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, 0.94], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 5, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 1, random.uniform(0.0, 0.05 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 9, random.uniform(0.0, 0.5 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["C'"] = pd.Series([3 + 10, 9, random.uniform(0.52, 0.7 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 10.0, random.uniform(0.5 + 2 * mra_v_pu, 0.7 - 2 * mra_v_pu)],
                                                index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, random.uniform(0.88 + 2 * mra_v_pu, 1.0)], index=index)

        # TABLE 7 - CATEGORY II HVRT TEST CONDITION
        elif CAT_2 in current_mode and HV in current_mode:
            # ABCDE
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 10, 1.0], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.2, 1.2 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.3, 1.175], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 0.5, 1.15], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, 1.0], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 10, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 0.2, random.uniform(1.18, 1.2)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 0.3, random.uniform(1.155, 1.175)], index=index)
                TEST_CONDITION["D"] = pd.Series([4, 0.5, random.uniform(1.13, 1.15)], index=index)
                TEST_CONDITION["E"] = pd.Series([5, 120.0, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)

        # TABLE 8 - CATEGORY III HVRT TEST CONDITION
        elif CAT_3 in current_mode and HV in current_mode:
            # ABB'C
            if RANGE_STEPS == "Figure":
                TEST_CONDITION["A"] = pd.Series([1, 5, 1.05], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 12, 1.2 - 2 * mra_v_pu], index=index)
                TEST_CONDITION["B'"] = pd.Series([2 + 10, 12, 1.12], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 120, 1.05], index=index)
            elif RANGE_STEPS == "Random":
                TEST_CONDITION["A"] = pd.Series([1, 5, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
                TEST_CONDITION["B"] = pd.Series([2, 12, random.uniform(1.18, 1.2)], index=index)
                TEST_CONDITION["B'"] = pd.Series([2 + 10, 12, random.uniform(1.12, 1.2)], index=index)
                TEST_CONDITION["C"] = pd.Series([3, 120, random.uniform(1.0, 1.1 - 2 * mra_v_pu)], index=index)
        '''
        Get the full test sequence :
        Example for CAT_2 + LV + Not Consecutive
                ___________________________________________________
        VRT_CONDITION  MIN_DURATION  VRT_VALUES  VRT_START_TIMING  VRT_END_TIMING
        1.0         10.00        0.94              0.00           10.00
        2.0          0.16        0.28             10.00           10.16
        3.0          0.16        0.43             10.16           10.32
        4.0          2.68        0.65             10.32           13.00
        5.0          2.00        0.88             13.00           15.00
        6.0        120.00        0.94             15.00          135.00

                Example for CAT_3 + HV + Consecutive
                ___________________________________________________
        VRT_CONDITION  MIN_DURATION  VRT_VALUES  VRT_START_TIMING  VRT_END_TIMING
        1.0           5.0        1.05               0.0             5.0
        2.0          12.0        1.20               5.0            17.0
        1.0           5.0        1.05              17.0            22.0
        2.0          12.0        1.20              22.0            34.0
        1.0           5.0        1.05              34.0            39.0
        2.0          12.0        1.20              39.0            51.0
        3.0         120.0        1.05              51.0           171.0
        1.0           5.0        1.05             171.0           176.0
        12.0         12.0        1.14             176.0           188.0
        3.0         120.0        1.05             188.0           308.0

        Note: The Test condition value is directly connected to the alphabetical order.
        The value 1.0 is for A, 2.0 is for B and so on. When a prime is present, we
        just add the value 10.0. The value 12.0 is for B', 13 is for C' and so on.
        The idea is just to show this on the data.
        '''
        test_sequences_df = self.get_test_sequence(current_mode, TEST_CONDITION)

        return test_sequences_df

    def execute_postprocess(self):
        if wav_ena:
            # Convert and save the .mat file
            ts.log('Processing waveform dataset(s)')
            wave_start_filename = dataset_filename + "_WAV.csv"

            ds = daq.waveform_capture_dataset()  # returns list of databases of waveforms (overloaded)
            ts.log(f'Number of waveforms to save {len(ds)}')
            if len(ds) > 0:
                ds[0].to_csv(ts.result_file_path(wave_start_filename))
                ts.result_file(wave_start_filename)

        if data_ena:
            ds = daq.data_capture_dataset()
            ts.log('Saving file: %s' % rms_dataset_filename)
            ds.to_csv(ts.result_file_path(rms_dataset_filename))
            ds.remove_none_row(ts.result_file_path(rms_dataset_filename), "TIME")
            result_params = {
                'plot.title': rms_dataset_filename.split('.csv')[0],
                'plot.x.title': 'Time (sec)',
                'plot.x.points': 'TIME',
                'plot.y.points': 'AC_VRMS_1, AC_VRMS_2, AC_VRMS_3',
                'plot.y.title': 'Voltage (V)',
                'plot.y2.points': 'AC_IRMS_1, AC_IRMS_2, AC_IRMS_3',
                'plot.y2.title': 'Current (A)',
            }
            ts.result_file(rms_dataset_filename, params=result_params)
        result_summary.write('%s, %s, %s,\n' % (dataset_filename, wave_start_filename,
                                                rms_dataset_filename))

        pass
