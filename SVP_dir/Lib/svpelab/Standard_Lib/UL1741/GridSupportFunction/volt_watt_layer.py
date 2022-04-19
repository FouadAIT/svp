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
from svpelab.Standard_Lib.UL1741.UL1741SB_layer import UL1741SBLayer
from svpelab.Standard_Lib.IEEE1547.GridSupportFunction.volt_watt_layer import VoltWatt

class VoltWatt(UL1741SBLayer,VoltWatt):
    def __init__(self, ts, function='Volt-Watt', imbalance_angle_fix=None):
        super().__init__(ts, function, imbalance_angle_fix=imbalance_angle_fix)
        self.name = 'Volt-Watt'


    def create_dict_steps(self):
        """
        This function creates the dictionary steps for Volt-Watt based on UL1741 SB4.3.5.14.9
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
            # Requirements in ii)
            """
            In the procedure in IEEE 1547.1-2020 Section 5.14.9.2, there are some iterations in which the
            steps are at the same voltage level - for example going from step (s) back to step (g) as part of the
            iterations required in steps (t) and (u), or where V2 = VH. In such cases it is not required to judge
            criteria for both (s) and (g) during those iterations.
            """
            if v_pairs['V2'] == self.v_high:
                del v_steps_dict['Step S']
                del v_steps_dict['Step G']

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

