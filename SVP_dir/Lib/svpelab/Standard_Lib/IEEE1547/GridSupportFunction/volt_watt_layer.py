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
from svpelab.Standard_Lib.IEEE1547.IEEE1547_layer import IEEE1547dot1Layer
import re

class VoltWatt(IEEE1547dot1Layer):
    def __init__(self, ts, function='Volt-Watt'):
        super().__init__(ts, function)
        self.name = 'Volt-Watt'
        self.ts.slow_functions = True

    def create_configuration_variables(self):
        """
        This function creates the dictionary steps for Volt-Watt
        :param mode (string): Verifies if VW is operating under normal or imbalanced grid mode
        :return: vw_dict_steps (dictionary)
        """
        self.mode = self.ts.param_value('vw.mode')
        """
        Test Configuration
        """
        # list of active tests
        vw_curves = []
        imbalance_test = False
        self.vw_response_time = {}
        if self.mode == 'Imbalanced grid':
            """
            imbalance_resp = []
            if ts.param_value('eut.imbalance_resp') == 'EUT response to the individual phase voltages':
                imbalance_resp.append('INDIVIDUAL_PHASES_VOLTAGES')
            elif ts.param_value('eut.imbalance_resp') == 'EUT response to the average of the three-phase effective (RMS)':
                imbalance_resp.append('AVG_3PH_RMS')
            else:  # 'EUT response to the positive sequence of voltages'
                imbalance_resp.append('POSITIVE_SEQUENCE_VOLTAGES')
            """
            self.imbalance_test = True
            vw_curves.append(1)
            self.vw_response_time[1] = float(self.ts.param_value('vw.test_1_tr'))

        else:
            self.imbalance_test = False

            if self.ts.param_value('vw.test_1') == 'Enabled':
                vw_curves.append(1)
                self.vw_response_time[1] = float(self.ts.param_value('vw.test_1_tr'))
            if self.ts.param_value('vw.test_2') == 'Enabled':
                vw_curves.append(2)
                self.vw_response_time[2] = float(self.ts.param_value('vw.test_2_tr'))
            if self.ts.param_value('vw.test_3') == 'Enabled':
                vw_curves.append(3)
                self.vw_response_time[3] = float(self.ts.param_value('vw.test_3_tr'))

        # List of power level for tests
        irr = self.ts.param_value('vw.power_lvl')
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

        self.set_imbalance_config( imbalance_angle_fix= self.ts.param_value('vw.imbalance_fix'))

        loops = []
        for vw_curve in vw_curves:
            for power in pwr_lvls:
                loops.append(f"CRV{vw_curve}_PWR{power}")
        self.ts.log_debug(f'VW mode ={self.mode}')
        return loops



    def set_loop_test_procedure_configuration(self, loop):
        self.set_curve(int(re.search('(?<=CRV)[0-9]+', loop).group()))
        self.set_pwr_setting(pwr=float(re.search('(?<=PWR)[0-9]+.[0-9]+', loop).group()))
        self.set_time_settings(tr=self.vw_response_time[self.get_curve()], number_tr=4)

    # ActiveFunction.set_curve()
    # ActiveFunction.set_time_settings()
    def set_test_bench_equipment(self):
        self.set_grid_to_nominal()

        self.set_dc_pwr(irr=1100, pwr=self.get_pwr())

        self.vw_config_to_eut()

    def create_dict_steps(self):
        """
        This function creates the dictionary steps for Volt-Watt
        :param mode (string): Verifies if VW is operating under normal or imbalanced grid mode
        :return: vw_dict_steps (dictionary)
        """

        v_steps_dict = None
        self.ts.log_debug(50*f'=')
        self.ts.log_debug(f'Imbalance test={self.imbalance_test}')
        self.ts.log_debug(50*f'=')
        if self.imbalance_test == False:
            # Setting starting letter for label

            self.set_step_label('G')
            #self.ts.log_debug(f'STEP={self.step_label}')

            v_steps_dict = collections.OrderedDict()
            v_pairs = self.standard_dict[self.cat][f'curve{self.curve}']['VALUES']
            #self.ts.log_debug(f'VPAIRS={v_pairs}')

            a_v = self.MRA['V'] * 1.5
            # Step G
            v_steps_dict[self.get_step_label()] = {'V': self.v_low + a_v}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V1']*self.v_nom - a_v}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V1']*self.v_nom + a_v}
            v_steps_dict[self.get_step_label()] = {'V': (v_pairs['V2']*self.v_nom + v_pairs['V1']*self.v_nom) / 2}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V2']*self.v_nom - a_v}
            # Step K
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V2']*self.v_nom + a_v}
            v_steps_dict[self.get_step_label()] = {'V': self.v_high - a_v}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V2']*self.v_nom + a_v}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V2']*self.v_nom - a_v}
            # Step P
            v_steps_dict[self.get_step_label()] = {'V': (v_pairs['V1']*self.v_nom + v_pairs['V2']*self.v_nom) / 2}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V1']*self.v_nom + a_v}
            v_steps_dict[self.get_step_label()] = {'V': v_pairs['V1']*self.v_nom - a_v}
            v_steps_dict[self.get_step_label()] = {'V': self.v_low + a_v}

            if v_pairs['V2'] > self.v_high:
                del v_steps_dict['Step K']
                del v_steps_dict['Step L']
                del v_steps_dict['Step M']
                del v_steps_dict['Step N']
                del v_steps_dict['Step O']

            # Ensure voltage step doesn't exceed the EUT boundaries and round V to 2 decimal places
            for step, step_dict in v_steps_dict.items():
                v_steps_dict.update({step: {'V': np.around(step_dict['V'], 2)}})
                if step_dict['V'] > self.v_high:
                    self.ts.log("{0} voltage step (value : {1}) changed to VH (v_high)".format(step, step_dict['V']))
                    v_steps_dict.update({step: {'V': self.v_high}})
                elif step_dict['V'] < self.v_low:
                    self.ts.log("{0} voltage step (value : {1}) changed to VL (v_low)".format(step, step_dict['V']))
                    v_steps_dict.update({step: {'V': self.v_low}})

            #self.ts.log_debug('curve points:  %s' % v_pairs)


        elif self.imbalance_test:
            self.set_step_label('G')
            v_steps_dict = collections.OrderedDict()
            v_steps_dict[self.get_step_label()] = {'V': 'case_a'}
            v_steps_dict[self.get_step_label()] = {'V': self.v_nom}
            v_steps_dict[self.get_step_label()] = {'V': 'case_b'}
            v_steps_dict[self.get_step_label()] = {'V': self.v_nom}
        self.ts.log_debug(50*f'=')
        self.ts.log_debug(f'STEP_DICTIONARY={v_steps_dict}')
        self.ts.log_debug(50*f'=')

        self.steps_dict = v_steps_dict


    def vw_config_to_eut(self):

        v_pairs = self.standard_dict[self.cat][f'curve{self.curve}']['VALUES']

        if self.ts.equipments["eut"] is not None:
            vw_curve_params = {'v': [v_pairs['V1']/self.v_nom,
                                        v_pairs['V2']/self.v_nom],
                                'w': [v_pairs['P1']/self.p_rated,
                                        v_pairs['P2']/self.p_rated],
                                'DeptRef': 'W_MAX_PCT',
                                "RmpTms":self.tr}

            #vw_params = {'Ena': True, 'ActCrv': 1, 'curve': vw_curve_params}
            vw_params = {'Ena': True, 'ActCrv': self.curve, 'curve': vw_curve_params}

            self.ts.log_debug('Writing the following params to EUT: %s' % vw_params)
            self.ts.equipments["eut"].volt_watt(params=vw_params)

            '''
            f) Verify volt-watt mode is reported as active and that the correct characteristic is reported.
            '''
            self.ts.log_debug('Initial EUT VW settings are %s' % self.ts.equipments["eut"].volt_watt())