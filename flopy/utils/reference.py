"""
Module spatial referencing for flopy model objects

"""
import os

__all__ = [
    "TemporalReference",
    "read_attribs_from_namfile_header",
    "read_usgs_model_reference_file",
]
# all other classes and methods in this module are deprecated


def read_attribs_from_namfile_header(namefile: str) -> dict:
    """Check for reference info in the nam file header"""
    caster = {  # Specify types for the values read
        "xll": float,
        "yll": float,
        "xul": float,
        "yul": float,
        "rotation": float,
        "epsg": int,
        "proj4_str": str,
        # The following keys all map to the same attribtue, prior behavior 
        # allowed for anything starting with the characters `start`
        "start_date": str,
        "start_datetime": str,
        "start": str
    }
    header = []
    ref = dict()
    with open(namefile, "r") as f:
        for line in f:
            if not line.startswith("#"):
                break
            header.extend(line.strip().replace("#", "").split(";"))

    header = [s.split(":") for s in header]
    for key, *item in header:
        if key not in ["proj4_str"]:
            item = item[0]
        else:  # proj4_str might have : character
            item = ":".join(item)

        try:  # Values provided might not match type
            val = caster[key](item)  # Case sensitive
            if val == "none":  # proj4_str might have none, given as string
                val = None
            ref[key] = val
        except ValueError:
            pass

    return ref


def read_usgs_model_reference_file(reffile = "usgs.model.reference") -> dict:
    """read spatial reference info from the usgs.model.reference file
    https://water.usgs.gov/ogw/policy/gw-model/modelers-setup.html"""
    caster = {  # Specify types for the values read
        "xll": float,
        "yll": float,
        "xul": float,
        "yul": float,
        "rotation": float,
        "epsg": int,
        "proj4": str,
        "start_date": str,
    }
    ref = dict()
    # Assumed to exist, checked by calling methods
    with open(reffile) as input:  
        for line in input:
            # Empty or comment
            if (len(line) <= 1) or (line.strip()[0] == "#"):  
                continue
            # Remove comments, split into key data
            key, *data = line.strip().split("#")[0].strip().split()
            if len(data) >= 1:
                # future proof, some values may be lists
                data = " ".join(data)
                if key in caster:  # Case sensitive
                    ref[key] = caster[key](data)
    
    return ref


class TemporalReference:
    """
    For now, just a container to hold start time and time units files
    outside of DIS package.
    """

    defaults = {"itmuni": 4, "start_datetime": "01-01-1970"}

    itmuni_values = {
        "undefined": 0,
        "seconds": 1,
        "minutes": 2,
        "hours": 3,
        "days": 4,
        "years": 5,
    }

    itmuni_text = {v: k for k, v in itmuni_values.items()}

    def __init__(self, itmuni=4, start_datetime=None):
        self.itmuni = itmuni
        self.start_datetime = start_datetime

    @property
    def model_time_units(self):
        return self.itmuni_text[self.itmuni]
