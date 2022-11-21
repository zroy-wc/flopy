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
        period_data: dict | None=None,
        time_units: str="days",
        start_datetime: str | np.datetime64 | None=None,  # YYYY-mm-ddTHH:MM:SS
        steady_state: bool | None=None,
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
    
    @start_datetime.setter
    def start_datetime(self, value: str | np.datetime64):
        self._start_datetime = value
    
    @property
    def start_date(self):
        """start_date is not tracked separately from start_datetime, attempt to
        return just the date using numpy.timedelta64, or str.split('T')[0]"""
        sdt = self._start_datetime
        if isinstance(sdt, np.datetime64):  # Remove date part for just time
            time = sdt - sdt.astype('datetime64[D]').astype(sdt.dtype)
            return sdt - time
        elif isinstance(sdt, str) and ('T' in sdt):
            return sdt.split('T')[0]
        else:
            msg = "current self.start_datetime type does not support date-only\
                 manipulation, try casting to numpy.datetime64 or str: {}"
            raise ValueError(msg.format(type(self._start_datetime)))
    
    @start_date.setter
    def start_date(self, value: str | np.timedelta64):
        sdt = self._start_datetime
        if sdt is None:
            sdt = value
        elif isinstance(sdt, str):
            assert isinstance(value, str)
            if 'T' in sdt:
                sdt = sdt.split('T')[-1]
            else:
                sdt = '00:00:00'
            sdt = value + 'T' + sdt  # drop old date
        elif isinstance(sdt, np.datetime64):
            assert isinstance(value, np.timedelta64)
            time = sdt - sdt.astype('datetime64[D]').astype(sdt.dtype)
            sdt = value + time
        self._start_datetime = sdt
    
    @property
    def start_time(self):
        """start_time is not tracked separately from start_datetime, attempt to 
        return just the time using numpy.timedelta64, or str.split('T')[-1]"""
        sdt = self._start_datetime
        if isinstance(sdt, np.datetime64):  # Remove date part for just time
            return sdt - sdt.astype('datetime64[D]').astype(sdt.dtype)
        elif isinstance(sdt, str) and ('T' in sdt):
            return sdt.split('T')[-1]
        else:
            msg = "current self.start_datetime type does not support time-only\
                 manipulation, try casting to numpy.datetime64 or str: {}"
            raise ValueError(msg.format(type(self._start_datetime)))
    
    @start_time.setter
    def start_time(self, value: str | np.timedelta64):
        sdt = self._start_datetime
        if sdt is None:
            sdt = '1970-1-1T00:00:00'  # default value
        if isinstance(sdt, str):
            assert isinstance(value, str)
            sdt = sdt.split('T')[0] + 'T' + value  # drop old time
        elif isinstance(sdt, np.datetime64):
            assert isinstance(value, np.timedelta64)
            sdt = sdt.astype('datetime64[D]').astype(sdt.dtype) + value
        self._start_datetime = sdt
    
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
            'start_date': ['start_date', 'start'],
            'start_time': ['start_time'],
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
        if not os.path.exists(reffile):
            return False
        ref = read_usgs_model_reference_file(reffile)
        get_from_file = {
            # attr name: key in file
            'start_date': 'start_date',
            'start_time': 'start_time',
            '_time_units': 'time_units',
        }
        for attr, ref_key in get_from_file.items():
            val = ref.get(ref_key, None)
            if val:
                setattr(self, attr, val)

        return True

