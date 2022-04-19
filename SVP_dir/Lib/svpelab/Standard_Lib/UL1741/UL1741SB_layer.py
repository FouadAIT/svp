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

from svpelab.Standard_Lib.IEEE1547.IEEE1547_layer import IEEE1547dot1Layer

UL1741SB_DEFAULT_ID = 'UL1741SB'


class UL1741Error(Exception):
    pass


def params(info, group_name=None, label='UL1741SB'):
    group_name = UL1741SB_DEFAULT_ID
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label=f'{label} Parameters', glob=True)

    # Automatic=Postprocessing will be ran automatically after the script is completed
    # Manual=Postprocessing will be ran independant from script based on previous results
    info.param(name('pp_ena'), label='Postprocessing', default='Disabled', values=['Enabled', 'Manual', 'Disabled'])
    info.param(name('file_location'), label='Results file location', default='/RESULT-FILES-LOCATIONS/HERE',
               active=name('pp_ena'), active_value=['Manual'])
    info.param(name('test_name'), label='Test name', default='Volt-Watt', values=['Volt-Watt', 'Volt-Var'],
               active=name('pp_ena'), active_value=['Manual'])


class UL1741SBLayer(IEEE1547dot1Layer):
    def __init__(self, ts, function=None, imbalance_angle_fix=None):
        # Import UL1741 standard curve points
        super().__init__(ts=ts, function=function, imbalance_angle_fix=imbalance_angle_fix)
        self.standard = UL1741SB_DEFAULT_ID
        ts.log_debug(f'FUNCTION1={function} in STANDARD={self.standard}')
        self.pp_ena = self.ts.param_value('UL1741SB.pp_ena')
        self.result_summary_filename = 'UL1741_summary.csv'



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
                # IEEE1547_dict = self.IEEE1547_obj.import_curvepoints(self.test_name)
                self.ts.log_debug('Postprocessing Starting')
                # self.standard_dict from ExtractDatapoints
                ul1741pp = postprocess.UL1741postprocessing(self.ts, self.standard_dict)
            else:
                self.ts.log_debug('Postprocessing is not available for this script test')
        elif self.pp_ena == 'Disabled':
            self.ts.log_debug('Postprocessing is disabled')







if __name__ == "__main__":
    pass
