from svpelab import gridsim
from svpelab import pvsim
from svpelab import das
from svpelab import der
from svpelab import hil


class EquipmentsLevel(object):
    
    #def __init__(self, ts, function=None, imbalance_angle_fix=None):
    def __init__(self, ts, **kw):
        self.ts = ts
        self.ts.equipments = {}
        self.ts.equipments["eut"] = None
        self.ts.equipments["grid"] = None
        self.ts.equipments["pv"] = None
        self.ts.equipments["hil"] = None

    def eut_init(self):
        """Eut initialization
        """

        self.ts.log_debug(15 * "*" + "EUT initialization" + 15 * "*")
        eut = der.der_init(self.ts, support_interfaces={'hil': self.ts.equipments["hil"]})
        self.ts.equipments["eut"] = eut
        if self.ts.equipments["eut"]is None:
            der.DERError(f'EUT is None')

        # self.v_nom = self.eut.v_nom()
        if self.ts.equipments["eut"] is not None:
            self.s_rated = self.ts.equipments["eut"].s_rated()
            self.v_high = self.ts.equipments["eut"].v_high()
            self.v_low = self.ts.equipments["eut"].v_low()
            self.v_in_nom = self.ts.equipments["eut"].v_in_nom()
            self.eut_startup_time = self.ts.equipments["eut"].startup_time()
            self.p_rated = self.ts.equipments["eut"].p_rated()
            self.phases = self.ts.equipments["eut"].phase()

            #Set MRA following parameters values ready
            self.MRA_settings()
            self.ts.log(f'{self.eut_startup_time} seconds EUT start up')
            self.ts.sleep(self.eut_startup_time)
            self.ts.equipments["eut"].config()
            self.ts.log_debug(self.ts.equipments["eut"].measurements())
            self.ts.log_debug(f'L/HVRT and trip parameters set to \
            the widest range : v_low: {self.v_low} V, v_high: {self.v_high} V')
            try:
                self.ts.equipments["eut"].vrt_stay_connected_high(
                    params={'Ena': True, 'ActCrv': 0, 'Tms1': 3000, 'V1': self.v_high, 'Tms2': 0.16, 'V2': self.v_high})
            except Exception as e:
                self.ts.log_error('Could not set VRT Stay Connected High curve. %s' % e)
            try:
                self.ts.equipments["eut"].vrt_stay_connected_low(
                    params={'Ena': True, 'ActCrv': 0, 'Tms1': 3000, 'V1': self.v_low, 'Tms2': 0.16, 'V2': self.v_low})
            except Exception as e:
                self.ts.log_error('Could not set VRT Stay Connected Low curve. %s' % e)

        else:
            self.ts.log_debug('Set L/HVRT and trip parameters set to the widest range of adjustability possible.')

    def MRA_settings(self):
        """MRA_settings [summary]
        """
        #TODO Finish table
        #TODO Link the table in the standard to the json
        self.MRA = {
            'V': 0.01 * self.v_nom,
            'Q': 0.05 * self.s_rated,
            'P': 0.05 * self.s_rated,
            'F': 0.01,
            'T': 0.01,
            'PF': 0.01
        }

    def chil_init(self):
        """HIL initialization function
        """
        self.ts.log_debug(15 * "*" + "HIL initialization" + 15 * "*")
        chil = hil.hil_init(self.ts)
        self.ts.equipments["hil"] = chil

        if self.ts.equipments["hil"] is not None:
            self.ts.equipments["hil"].config()


    def chil_start_simulation(self):
        if self.ts.equipments["hil"] is not None:
            self.ts.log('Start simulation of CHIL')
            self.ts.equipments["hil"].start_simulation()
            self.ts.log('10 seconds start up')
            self.ts.sleep(10)

    def set_parameters_on_hil(self, parameters):
        if self.ts.equipments["hil"] is not None:
            self.ts.log(f'Sending parameters {parameters} to HIL')
            self.ts.equipments["hil"].set_matlab_variables(parameters)
            self.ts.sleep(1)

    def get_chil_time(self):
        if self.ts.equipments["hil"] is not None:
            sim_time = self.ts.equipments["hil"].get_time()
        return sim_time

    def grid_init(self):
        """Initialize Grid simulator function
        """
        self.v_nom = self.ts.param_value('der.v_nom')

        self.ts.log_debug(15 * "*" + "grid simulator initialization" + 15 * "*")
        grid = gridsim.gridsim_init(self.ts, support_interfaces={'hil': self.ts.equipments["hil"]})  # Turn on AC so the EUT can be initialized
        self.ts.equipments["grid"] = grid

        if self.ts.equipments["grid"]  is not None:
            self.ts.equipments["grid"].voltage(self.v_nom)
            if self.ts.equipments["hil"]  is not None:  # If using HIL, give the grid simulator the hil object
                self.ts.equipments["grid"].config()


    def set_grid_to_nominal(self):
        """set_grid_nom Function to set the grid at the nominal voltage
        """
        # TODO : Add the frequency and phase angle as well
        if self.ts.equipments["grid"] is not None:
            self.ts.equipments["grid"].voltage(self.v_nom)


    def pv_init(self):
        """pv_init PV simulator initalization with the rated power level
        """
        self.ts.log_debug(15 * "*" + "PV simulator initialization" + 15 * "*")
        pv = pvsim.pvsim_init(self.ts, support_interfaces={'hil': self.ts.equipments["hil"]})
        self.ts.equipments["pv"] = pv

        if self.ts.equipments["pv"] is not None:
            self.ts.equipments["pv"].power_set(self.p_rated)
            self.ts.equipments["pv"].power_on()  
            self.ts.sleep(0.5)

    def set_dc_pwr(self, irr, pwr=None):
        if self.ts.equipments["pv"] is not None:
            if pwr is None:
                pv_power_setting = self.p_rated * self.pwr
            else:
                pv_power_setting = self.p_rated * pwr

            self.ts.equipments["pv"].iv_curve_config(pmp=pv_power_setting, vmp=self.v_in_nom)
            self.ts.equipments["pv"].irradiance_set(irr)

    def close_all_equipments(self):
        """Function to close all equipments if initiated
        """
        if self.ts.equipments["pv"] is not None:
            if self.p_rated is not None:
                self.ts.equipments["pv"].power_set(self.p_rated)
            self.ts.equipments["pv"].close()
        if self.ts.equipments["grid"] is not None:
            if self.v_nom is not None:
                self.ts.equipments["grid"].voltage(self.v_nom)
            self.ts.equipments["grid"].close()
        if self.ts.equipments["hil"] is not None:
            self.ts.equipments["hil"].close()
        if self.ts.equipments["eut"]  is not None:
            self.ts.equipments["eut"].close()