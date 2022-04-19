# Real-time plotting SVP
The Real-time plotting feature is an addition to the SVP Software. It is a parallel process that query the data in real-time from an ongoing test and show it in the way that the feature was configured.

**Insert a GIF of the RTP running**


## Installation
Please refer to the [Install section](https://github.com/sunspec/svp/blob/master/doc/INSTALL.md) for detailed instruction

Also, use the drivers that are in this repository and all scripts should be compatible with the feature.

## Usage
The particularity from the Real-time plotting feature is that it needed modification to OpenSVP itself, but also to some of its drivers related to the Data Acquisition System (DAS) and another specific driver was added. If the feature needs to be added to a new DAS driver, please refer to the 'Change to das_xxx.py' section.

Then, assuming having a good experience of OpenSVP, here are the first steps to use the feature:

 1. Start OpenSVP
 2. Import the corresponding directory (Drivers needs to be Real-time plotting compatible)
 3. Edit a test or suite.
	 a) Enable the Real-time plotting feature, which is in the data acquisition system parameters
	b) Open the Real-time plotting preference window by clicking on the "Real-Time Plotting Edit" button.
	c) Configure the feature (See section **How to configure** for details)
4. Run the test or suite.

Next, if changes are needed, redo steps 3 and 4 to adjust the feature.

## How to configure
After doing step 3. c) of the **Usage** section, the following window should appear:

![Default configuration](\README Images\RTP_Pref_1.jpg)

The first tab is the General preference tab and as default, "the Standard tested" should be set on "1547.1". This means that the configuration is already done by the 1547.1 standard drivers.

Then, for a **custom** configuration, select "Custom" as the "Standard tested".

![Custom General Preference window](RTP_Pref_2.jpg)
As it can be seen, there is more than one tab now and there is only one General Preference tab. The General Preference tab is where the overall layout of the Real-time plotting feature is configured. The user can select how many rows and columns the matrix of plots will have in the feature. Depending on the size of this matrix, tabs will appear or disappear.

Then, looking into the individual "Tab":
![individual "Tab"](RTP_Pref_3.jpg)
Here are the elements and their functionality in this tab:

 - The **Plot title** can be configure, which change the name of the "Tab" and also the name in the General Preference tab layout of the feature.
 - The **Row** and **Column** indicates the coordinate of the plot to be configured in the matrix layout of the feature.
 - The **Type of plot** is a drop down list, where the user select the type of plot to show. The user can select "XY", "Time-based" or "Disabled".
	 - "XY" will make appear the required parameters to configure an XY plot. (Example: Var(Volt) plot for a Volt-Var test of an inverter)
	 - "Time-based" will make appear the required parameters to configure a Time-based plot. (The X axis is related to time and the Y is selectable)
	 - "Disabled" is the default configuration where the plot is disabled.
After completing the configuration of each of the plot in the layout matrix, click "Ok" or "Apply" to save the configuration of the Real-time plotting feature associated to the test or suite configured.

### XY Plot configuration
 The Default XY plot tab looks like this:
 ![XY plot tab](RTP_Pref_4.jpg)
 The tab is divided in 3 sections :


 1. **The "Tab" Parameters** at the left part of the tab, where the value and data handling parameters are configured.
 2. **The Display** at the top right part of the tab is an example of the plot to be displayed in the feature.
 3. **The Display configuration** under the Display where visuals of the display are configured.

The new parameters in **The "Tab" Parameters** and their definition is as follows:

 - **Y1 axis value** and **Y2 axis value**: It is respectively the left and the right y axis electrical value. To configure it, click on the "Select values" button and the following pop-up window should appear. Where, the different specific values can be selected. (There is a maximum limit of 10 values selected)
 ![Y axis checkbox pop-up](RTP_Pref_5.jpg)
- **X axis value**: It is the generic type of electrical value to plot. The code implementation automatically link the correct signal. (For example, if "AC_P_1" is selected for the Y1 axis value and "V" for X axis value, the code will apply the AC_VRMS_1 as the X axis value for this specific plot )
- **Remove duplicates** and **Add filter**: If the "Remove duplicates" option is activated, the plot will only show the first type of data that the real-time plotting receives. It does that by filtering the data by its "events" column, which is defined inside the 1547.1 drivers or in the scripts depending on the version of OpenSVP. The "Add filter" button will make appear a new filter to apply to the filtering of data. Therefore, a specific recurrent event title can be applied. (For example, the string "_TR2" could be entered as filter and after clicking the "Apply" button, the plot will only show data that has the string ""_TR2" in its related event title.)

**The Display** cannot be modified directly. It is only there to show a preview of the configuration.

The new parameters in **The Display configuration** and their definition is as follows:

- **x axis title**, **y1 axis title** and **y2 axis title**: As seen on the display, those are the titles of the different axis.
- **With Grid** and **With Legend**: Enabled/Disabled the Grid and the Legend of the plot.
### Time-based Plot configuration
The Default Time-based plot tab looks like this:
 ![Time-based plot tab](RTP_Pref_6.jpg)
 As it can be seen, the tab is really similar to the XY plot tab. The differences are that the x axis value is fixed to the time value, there is not filtering of the data and the data can be displayed in different time boundaries.

Therefore, only new parameters is the **Time Display**, which can be:

- "Show everything": The plot will show every data points, while expending the x axis as the time is progressing.
- "Specific time window (s)": The plot will show only the past specified seconds of the data.  

### TO DO : complete the configuration of Time-based window 

## Changes to das_xxx.py


1. import RealTimePlotting_Connection:
	
 from . import RealTimePlotting_Connection as RTP
 
2. Add the Real-time plotting preference window button to the das params (Add the next code line at the end of the params function): 

 RTP.params(info, group_name=group_name + '.' + GROUP_NAME, active=gname('mode'), active_value=mode)
 
3. Retreive the rtp enable parameter and add it as an attribute to  the DAS class (Add the next code line in the DAS method init):

self.rtp_enable = self._param_value('rtp.rtp_enable')

4. Add the rtp connection to the DAS class attributes (Add the next code line at the end of the DAS method init):

self.rtp_conn = RTP.RealTimePlottingConnection(self.ts.run_conn, self.data_points)

5. Send data through the rtp connection when rtp enabled (Add the next code lines at the end of the DAS method device_data_read):

if self.rtp_enable:
            self.rtp_conn.Send_data(data)

6. Redefine the das.py DAS method data_capture to add a 'new capture enabled' flag signal send to rtp through the rtp connection (Add the following method to the DAS class):

	def data_capture(self, enable=True, channels=None):
        """
        Enable/disable data capture
        
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
        self.rtp_conn.New_data_capture(enable)