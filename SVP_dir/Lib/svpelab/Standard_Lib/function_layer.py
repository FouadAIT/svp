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

import json
import os
from svpelab.Standard_Lib.equipments_layer import EquipmentsLevel


class InitializationLayer(EquipmentsLevel):
    """ExtractDatapoints [summary]

    Parameters
    ----------
    object : [type]
        [description]
    """
    def __init__(self, ts, standard, function=None):
        super().__init__(ts=ts)
        #self.ts = ts
        self.accepted_std = ['IEEE1547dot1', 'UL1741SB']

        if standard in self.accepted_std :
            self.std_datapoints = standard
        else:
            raise self.ts.log_error(f'Standard must be either : {self.accepted_std}')

        self.name_dict = {
            'VV':'Volt-Var',
            'VW':'Volt-Watt'
            }
        self.full_name_unit = {
            'V': 'Voltage',
            'P': 'Active Power',
            'Q': 'Reactive Power',
            'F': 'Frequency',
            'PF': 'Power Factor',
            'I': 'Current'
        }

        self.ts.log_debug(f'FUNCTION={function}')
        if function is not None:
            self.test_name = function
        else:
            self.test_name = None
        self.standard_dict = self.import_curvepoints(function)

    def import_curvepoints(self, curve_name=None) -> dict:
        #TODO: Modify in order to remove hard coded library path
        """import_curvepoints [summary]

        Parameters
        ----------
        curve_name : string such as curve1, curve2 or curve3 (optional)
            It should indicate which curve to be selected if need as some
            test does not have multiple curve.

        Returns
        -------
        dict
            dictionary containing most information for executing test
        """


        self.ts.log_debug(f'Current Directory:{os.getcwd()}')
        self.ts.log_debug(f'Current file location: {os.path.dirname(os.path.abspath(__file__))}')
        if self.std_datapoints in ['IEEE1547dot1', 'IEEE1547', 'UL1741SB']:

            try:
                with open(f'{os.path.dirname(os.path.abspath(__file__))}\IEEE1547\CurvePoints\{curve_name}.json') as f:
                    self.curve_points_dict = json.load(f)
            except:
                raise self.ts.log_error("Curve_name JSON file doesn't exist in folder")
            self.ts.log_debug(f'DATA_POINTS={self.curve_points_dict}')

            if not("name" in self.curve_points_dict):
                raise self.ts.log_error('JSON Datapoints does not contain "name" key')
            elif not("measured_values" in self.curve_points_dict):
                raise self.ts.log_error('JSON Datapoints does not contain "measured_values" key')
            elif not("x_values" in self.curve_points_dict):
                raise self.ts.log_error('JSON Datapoints does not contain "x_values" key')
            elif not("y_values" in self.curve_points_dict):
                raise self.ts.log_error('JSON Datapoints does not contain "y_values" key')
            elif not("Category B" in self.curve_points_dict):
                raise self.ts.log_error('JSON Datapoints does not contain "Category B" key')

        specific_curve_dict = self.curve_points_dict

        return specific_curve_dict

    def get_dict(self):
        """Getter for steps

        Returns
        -------
        [type]
            [description]
        """
        return self.standard_dict
