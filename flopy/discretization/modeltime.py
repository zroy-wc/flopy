import os

import numpy as np

from ..utils.reference import (
    read_attribs_from_namfile_header,
    read_usgs_model_reference_file,
)


class ModelTime:
    """
    Class for MODFLOW simulation time

    Parameters
    ----------
    stress_periods : pandas dataframe
        headings are: perlen, nstp, tsmult
    temporal_reference : TemporalReference
        contains start time and time units information
    """

    def __init__(
        self,
        period_data=None,
        time_units="days",
        start_datetime=None,
        steady_state=None,
    ):
        self._period_data = period_data
        self._time_units = time_units
        self._start_datetime = start_datetime
        self._steady_state = steady_state

    @property
    def time_units(self):
        return self._time_units

    @property
    def start_datetime(self):
        return self._start_datetime
    
    @property
    def start_time(self):
        """start_time is not tracked separately from start_date, attempt to 
        return just the time using numpy.timedelta64"""
        if isinstance(self.start_datetime, np.datetime64):
            day = self.start_datetime\
                .astype('datetime64[D]')\
                .astype(self.start_datetime.dtype)
            return self.start_datetime - day  # just the time
        else:
            msg = "current self.start_datetime type does not support time-only\
                 manipulation, try casting to numpy.datetime64: {}"
            raise ValueError(msg.format(type(self._start_datetime)))
    
    @start_time.setter
    def start_time(self, value: np.datetime64):
        if isinstance(self.start_datetime, np.datetime64):
            day = self.start_datetime\
                .astype('datetime64[D]')\
                .astype(np.datetime64)
            self._start_datetime = day + value.astype(np.timedelta64)
        else:
            msg = "current self.start_datetime type does not support time-only\
                 manipulation, try casting to numpy.datetime64: {}"
            raise ValueError(msg.format(type(self._start_datetime)))

    @property
    def perlen(self):
        return self._period_data["perlen"]

    @property
    def nper(self):
        return len(self._period_data["perlen"])

    @property
    def nstp(self):
        return self._period_data["nstp"]

    @property
    def tsmult(self):
        return self._period_data["tsmult"]

    @property
    def steady_state(self):
        return self._steady_state

    @property
    def totim(self):
        delt = []
        perlen_array = self.perlen
        nstp_array = self.nstp
        tsmult_array = self.tsmult
        for ix, nstp in enumerate(nstp_array):
            perlen = perlen_array[ix]
            tsmult = tsmult_array[ix]
            for stp in range(nstp):
                if stp == 0:
                    if tsmult != 1.0:
                        dt = perlen * (tsmult - 1) / ((tsmult**nstp) - 1)
                    else:
                        dt = perlen / nstp
                else:
                    dt = delt[-1] * tsmult
                delt.append(dt)

        totim = np.add.accumulate(delt)
        return totim

    @property
    def tslen(self):
        n = 0
        tslen = []
        totim = self.totim
        for ix, stp in enumerate(self.nstp):
            for i in range(stp):
                if not tslen:
                    tslen = [totim[n]]
                else:
                    tslen.append(totim[n] - totim[n - 1])
                n += 1

        return np.array(tslen)
    
    def attribs_from_namfile_header(self, namefile):
        # check for reference info in the nam file header
        if namefile is None:
            return False
        ref = read_attribs_from_namfile_header(namefile)
        get_from_file = {
            # attr name: list of possible keys in file
            'start_datetime': [
                'start_datetime',
                'start_date',
                'start',
            ],
        }
        for attr, ref_keys in get_from_file.items():
            for ref_key in ref_keys:
                val = ref.get(ref_key, None)
                if val:
                    setattr(self, attr, val)
                    break  # Only set the first one found

        return True

    def read_usgs_model_reference_file(self, reffile="usgs.model.reference"):
        """read spatial reference info from the usgs.model.reference file
        https://water.usgs.gov/ogw/policy/gw-model/modelers-setup.html"""
        
        if os.path.exists(reffile):
            ref = read_usgs_model_reference_file(reffile)
            get_from_file = {
                # attr name: key in file
                'start_datetime': 'start_date',
                'start_time': 'start_time',
                '_time_units': 'time_units',
            }
            print(ref)
            for attr, ref_key in get_from_file.items():
                val = ref.get(ref_key, None)
                if val:
                    setattr(self, attr, val)
            
            return True
        else:
            return False
