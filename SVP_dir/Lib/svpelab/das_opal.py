"""

All rights reserved.

Questions can be directed to support@sunspec.org
"""

import os
from . import device_das_opal
from . import das
from . import RealTimePlotting_Connection as RTP
from . import dataset
MINIMUM_SAMPLE_PERIOD = 50

opal_info = {
    'name': os.path.splitext(os.path.basename(__file__))[0],
    'mode': 'Opal'
}


def das_info():
    return opal_info


def params(info, group_name=None):
    gname = lambda name: group_name + '.' + name
    pname = lambda name: group_name + '.' + GROUP_NAME + '.' + name
    mode = opal_info['mode']
    info.param_add_value(gname('mode'), mode)
    info.param_group(gname(GROUP_NAME), label='%s Parameters' % mode,
                     active=gname('mode'),  active_value=mode, glob=True)

    info.param(pname('sample_interval'), label='Sample Interval (ms)', default=1000)
    info.param(pname('map'), label='Opal Analog Channel Map (e.g. simulinks blocks, etc,.)', default='IEEE1547_VRT')
    info.param(pname('wfm_dir'), active_value= "Yes",label='Waveform Directory', default='C:\\Users\\DETLDAQ\\OPAL-RT\\'
                                                                     'RT-LABv2019.1_Workspace\\'
                                                                     'IEEE_1547.1_Phase_Jump\\models\\'
                                                                     'Phase_Jump_A_B_A\\phase_jump_a_b_a_sm_source\\'
                                                                     'OpREDHAWKtarget\\')
    info.param(pname('wfm_chan_list'),  label='Waveform Channel List', default='PhaseJump')
    info.param(pname('data_name'), label='Waveform Data File Name (.mat)', default='Data.mat')
    RTP.params(info, group_name=group_name + '.' + GROUP_NAME, active=gname('mode'), active_value=mode)

GROUP_NAME = 'opal'


class DAS(das.DAS):

    def __init__(self, ts, group_name, points=None, sc_points=None, support_interfaces=None):
        das.DAS.__init__(self, ts, group_name, points=points, sc_points=sc_points,
                         support_interfaces=support_interfaces)
        self.params['ts'] = ts
        self.params['map'] = self._param_value('map')
        self.params['sample_interval'] = self._param_value('sample_interval')
        self.params['wfm_dir'] = self._param_value('wfm_dir')
        self.params['wfm_chan_list'] = self._param_value('wfm_chan_list')
        self.params['data_name'] = self._param_value('data_name')
        if self.hil is None:
            ts.log_warning('No HIL support interface was provided to das_opal.py')
        self.params['hil'] = self.hil
        self.params['gridsim'] = self.gridsim
        self.params['dc_measurement_device'] = self.dc_measurement_device
        self.rtp_enable = self._param_value('rtp.rtp_enable')


        self.device = device_das_opal.Device(self.params)
        self.data_points = self.device.data_points

        # initialize soft channel points
        self._init_sc_points()
        if self.params['sample_interval'] is not None:
            if self.params['sample_interval'] < 50 and self.params['sample_interval'] is not 0:
                raise das.DASError('Parameter error: sample interval must be at least 50 ms or 0 for manual sampling')
        try :
            self.rtp_conn = RTP.RealTimePlottingConnection(self.ts.run_conn, self.data_points)
        except:
            print("No Real-Time plotting capabilities on SVP")

    def _param_value(self, name):
        return self.ts.param_value(self.group_name + '.' + GROUP_NAME + '.' + name)

    def set_dc_measurement(self, obj=None):
        """
        DEPRECATED

        In the event that DC measurements are taken from another device (e.g., a PV simulator) please add this
        device to the das object
        :param obj: The object (e.g., pvsim) that will gather the dc measurements
        :return: None
        """
        # self.ts.log_debug('device: %s, obj: %s' % (self.device, obj))
        self.device.set_dc_measurement(obj)
    def device_data_read(self):
        """
        Read the current data values directly from the DAS. It does not create a new data sample in the
        data capture, if active.
        """
        data = self.device.data_read()
        # add soft channel points
        for p in self.sc_data_points:
            data.append(self.sc[p])
        try:
            if self.rtp_enable:
                self.rtp_conn.Send_data(data)
        except:
            print("No Real-Time plotting capabilities on SVP")
            
        return data

    def data_capture(self, enable=True, channels=None):
        """
        Enable/disable data capture.

        If sample_interval == 0, there will be no autonomous data captures and self.data_sample should be used to add
        data points to the capture
        """
        if self.device is not None:
            self.sample_interval = self.device.sample_interval
        if enable is True:
            if self._capture is False:
                self._ds = dataset.Dataset(self.data_points, ts=self.ts)
                self._last_datarec = []
                if self.sample_interval > 0:
                    if self.sample_interval < MINIMUM_SAMPLE_PERIOD:
                        raise DASError('Sample period too small: %s' % (self.sample_interval))
                    self._timer = self.ts.timer_start(float(self.sample_interval)/1000, self._timer_timeout,
                                                      repeating=True)
                self._capture = True
        elif enable is False:
            if self._capture is True:
                if self._timer is not None:
                    self.ts.timer_cancel(self._timer)
                self._timer = None
                self._capture = False
        self.device.data_capture(enable)
        try:
            self.rtp_conn.New_data_capture(enable)
        except:
            print("No Real-Time plotting capabilities on SVP")


if __name__ == "__main__":

    pass


