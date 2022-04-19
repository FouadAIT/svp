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
import numpy as np

def get_cols(meas):
    type_meas_dict = {
        'V': 'AC_VRMS',
        'I': 'AC_IRMS',
        'P': 'AC_P',
        'S': 'AC_S',
        'Q': 'AC_Q',
        'PF': 'AC_PF',
        'F': 'AC_FREQ'
    }
    if meas in type_meas_dict:
        return type_meas_dict[meas]
    else:
        raise KeyError('Measurement Type not present in dictionary')


def strip_cols(df):
    col_dict={}
    for col in df.columns:
        col_dict[col]=col.strip()
    renamed_df = df.rename(columns=col_dict)
    return renamed_df


def aggregate_meas(ts, df, type_meas, phase=3):
    """aggregate_meas Function to aggregate measurements into sum or average
    depending on type of measurement

    Parameters
    ----------
    df : Dataframe
        Dataframe contaning measurements from DAS
    type_meas : string
        String from 'V', 'I', 'P', 'Q', 'S', 'F', 'PF'
    phase : int, optional
        number of phase of the config, by default 3

    Returns
    -------
    Dataframe
        Dataframe containing the new aggregated measured values
    """
    cols = []
    key = get_cols(type_meas)
    for i in range(1, phase+1):
        cols.append(f'{key}_{i}')

    if type_meas in ['P', 'S', 'Q', 'I']:
        df[f'{type_meas}_MEAS'] = df.loc[:, cols].sum(axis=1)
    else:
        df[f'{type_meas}_MEAS'] = df.loc[:, cols].sum(axis=1).div(phase)
    return df
    