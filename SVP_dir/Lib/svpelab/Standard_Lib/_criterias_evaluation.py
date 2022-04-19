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
            
import numpy as np
from svpelab import der
from svpelab.der import DERError


def eval_min_max(self, value):
    """Evaluate minimum and maximum following the IEEE X & Y(X) criterias function

    Parameters
    ----------
    value : float/int
        the desired value needed to calculate minimum and maximum from

    Returns
    -------
    float/int
        returns minimum and maximum target for the specified value based on X and Y configuration
        of the function
    """
    self.ts.log_debug(f'MRA_X_{self.x}={self.MRA[self.x]}')
    self.ts.log_debug(f'MRA_Y_{self.y}={self.MRA[self.y]}')

    target_min = self.interpolate_value(meas_value=value + self.MRA[self.x] * 1.5) - (self.MRA[self.y] * 1.5)
    target_max = self.interpolate_value(meas_value=value - self.MRA[self.x] * 1.5) + (self.MRA[self.y] * 1.5)
    target = self.interpolate_value(meas_value=value )

    return target_min,  target_max , target

def interpolate_value(self, meas_value):
    """Intepolate function for curve related values

    Parameters
    ----------
    meas_value : float/int
        the desired value for the interpolation

    Returns
    -------
    float
        value followed by the interpolation function
    """
    x = []
    y = []
    self.ts.log_debug(f'self.curve : {self.curve}')
    self.ts.log_debug(f'self.datapoints_dict : {self.datapoints_dict}')

    x_ref = self.datapoints_dict[self.cat][f'curve{self.curve}'][self.x]
    y_ref = self.datapoints_dict[self.cat][f'curve{self.curve}'][self.y]
    self.ts.log_debug(f'Value={meas_value}')
    for key, value in self.datapoints_dict[self.cat][f'curve{self.curve}']['VALUES'].items():
        if self.x in key:
            x.append(value*self.reference_unit(x_ref))
        elif self.y in key:
            y.append(value*self.reference_unit(y_ref))
    self.ts.log_debug(f"X={x}")
    self.ts.log_debug(f"Y={y}")

    q_value = float(np.interp(meas_value, x, y))
    self.ts.log_debug(f"INTERPOLATED_VALUES={q_value}")

    return round(q_value, 1)

def reference_unit(self, type_value):
    """This function will determinate the reference value for the points needed

    Parameters
    ----------
    type_value : string
        value can be either v_nom, var_rated, s_rated, etc.

    Returns
    -------
    float value from eut parameters
    """
    #self.ts.log_debug(f'Type_value={type_value}')
    if 'v_nom' in type_value:
        return self.eut.v_nom()
    elif 'var_rated' in type_value:
        return self.eut.var_rated()
    elif 's_rated' in type_value:
        return self.eut.s_rated()
    elif 'p_rated' in type_value:
        return self.eut.p_rated()

