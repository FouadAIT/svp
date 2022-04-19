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

import pandas as pd


REALTIME_PLOTTING_CONNECTION_DEFAULT_ID = 'rtp'

rtp_modules = {}

def params(info, id=None, label='Real-Time Plotting', group_name=None, active=None, active_value=None):
    if group_name is None:
        group_name = REALTIME_PLOTTING_CONNECTION_DEFAULT_ID
    else:
        group_name += '.' + REALTIME_PLOTTING_CONNECTION_DEFAULT_ID
    if id is not None:
        group_name += '_' + str(id)
    print('group_name = %s' % group_name)
    name = lambda name: group_name + '.' + name
    info.param_group(group_name, label='%s Parameters' % label, glob=True)
    print('name = %s' % name('mode'))
    info.param(name('rtp_enable'), label='Real-time Plotting', default='Disabled', values=['Enabled', 'Disabled'])
    info.param(name('realtime_plotting_edit'), label='Real-Time Plotting Edit', active=name('rtp_enable'),
               active_value='Enabled', default='OnRtp', values=['OnRtp'], ptype='button')
    for mode, m in rtp_modules.items():
        m.params(info, group_name=group_name)

class RealTimePlottingConnection:
    def __init__(self, rtp_conn=None, data_points=None, das=None):

        self.conn = rtp_conn
        self.data_points = data_points
        print(das)

    def Send_data(self, data):
        if self.conn is not None:
            if self.conn.poll() is True:
                msg = self.conn.recv()
                if msg == 'terminate':
                    self.conn.close()
                    self.conn = None
            else:
                serie = pd.Series(data[1:], index=self.data_points[1: len(data)], name=data[0])
                self.conn.send({'name': 'Data', 'data': serie})
        else:
            pass

    def New_data_capture(self, enable):

        if enable is True and self.conn is not None:
            print(f"Type of self.conn : {self.conn}")
            self.conn.send({'name': 'new XY'})
        else:
            pass
