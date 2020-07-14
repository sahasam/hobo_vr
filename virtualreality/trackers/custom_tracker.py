import asyncio
import math
import sys
from copy import copy
import numpy as np
import serial
import serial.threaded
import pyrr
from pyrr import Quaternion
from docopt import docopt

from ..util import utilz as u
from .. import __version__
from .. import templates
from ..calibration.manual_color_mask_calibration import CalibrationData
from ..calibration.manual_color_mask_calibration import colordata_to_blob
from ..calibration.manual_color_mask_calibration import load_mapdata_from_file
from ..server import server
from ..templates import ControllerState


class Poser(templates.PoserTemplate):
    """A pose estimator."""

    def __init__(self, *args, camera=4, width=-1, height=-1, calibration_file=None, calibration_map_file=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.serialpaths = {"hmd" : "COM4", "contr_l" : "COM5"}
        
    @templates.thread_register(1/50)
    async def get_hmd_orientation(self) :
        h = 0
        with serial.Serial(self.serialpaths["hmd"], 115200, timeout=1 / 4) as ser:
            with serial.threaded.ReaderThread(ser, u.SerialReaderFactory) as protocol:
                while self.coro_keep_alive["get_hmd_orientation"][0] :
                    try:
                        gg = u.get_numbers_from_text(protocol.last_read)

                        if len(gg) > 0 :
                            (w, x, y, z, m) = gg

                            print(gg)

                            self.pose.r_w = round(w, 5)
                            self.pose.r_x = round(x, 5)
                            self.pose.r_y = round(y, 5)
                            self.pose.r_z = round(z, 5)

                        self.pose["y"] = round(np.sin(h), 4)
                        self.pose["x"] = round(np.cos(h), 4)
                        self.pose["z"] = round(np.cos(h), 4)

                        h += 0.01

                    except Exception as e:
                        print(f"{self.get_hmd_orientation.__name__}: {e}")
                        break
                    
                    await asyncio.sleep(self.coro_keep_alive["get_hmd_orientation"][1])
                        
    
    @templates.thread_register(1/50)
    async def get_controller_orientation(self) :
        with serial.Serial(self.serialpaths["contr_l"], 115200, timeout=1 / 4) as ser:
            with serial.threaded.ReaderThread(ser, u.SerialReaderFactory) as protocol:
                while self.coro_keep_alive["get_controller_orientation"][0] :
                    try:
                        gg = u.get_numbers_from_text(protocol.last_read)

                        if len(gg) > 0 :
                            (w, x, y, z) = gg

                            self.pose_controller_r.r_w = round(w, 5)
                            self.pose_controller_r.r_x = round(x, 5)
                            self.pose_controller_r.r_y = round(y, 5)
                            self.pose_controller_r.r_z = round(z, 5)
                    except exception as e:
                        print(f"{self.get_controller_orientation.__name__}: {e}")
                        break

                    await asyncio.sleep(self.coro_keep_alive["get_controller_orientation"][1])

def main():
    argv = sys.argv[1:]
    if sys.argv[1] != "custom-tracker" :
        argv = ["track"] + argv

    #args = docopt(__doc__, version=f"pyvr version {__version__}", argv=argv)

    t = Poser(send_delay=1/50)
    asyncio.run(t.main())

