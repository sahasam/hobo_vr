"""
this is an example of using virtualreality.templates

to get basic overview of virtualreality.templates.PoserClient run this in your python interpreter:
    help(virtualreality.templates.PoserClient)

to get more info on virtualreality.templates.PoserTemplate run this in your python interpreter:
    help(virtualreality.templates.PoserTemplate)

or visit https://github.com/okawo80085/hobo_vr/blob/master/examples/poserTemplate.py

more examples/references:
    https://github.com/okawo80085/hobo_vr/blob/master/virtualreality/trackers/color_tracker.py

"""

import asyncio
import time
import numpy as np
import pyrr
import serial

from virtualreality import templates
from virtualreality.server import server
from virtualreality.util import utilz as u

poser = templates.PoserClient(send_delay=1/50)

@poser.thread_register(1/50)
async def example_thread():
    h = 0
    with serial.Serial("COM4", 115200, timeout=1 / 4) as ser:
        with serial.threaded.ReaderThread(ser, u.SerialReaderFactory) as protocol:
            while poser.coro_keep_alive["example_thread"][0]:
                try:
                    gg = u.get_numbers_from_text(protocol.last_read)
                    print(protocol.last_read)

                    if len(gg) > 0 :
                        (w,x,y,z) = gg
                        print(gg)
                        poser.pose["y"] = round(np.sin(h), 4)
                        poser.pose["x"] = round(np.cos(h), 4)
                        poser.pose["z"] = round(np.cos(h), 4)

                        poser.pose_controller_l["y"] = 1
                        poser.pose_controller_l["x"] = 1
                        poser.pose_controller_l["z"] = 1

                        poser.pose.r_x = round(x, 4)
                        poser.pose.r_y = round(y, 4)
                        poser.pose.r_z = round(z, 4)
                        poser.pose.r_w = round(w, 4)

                        poser.pose_controller_l.r_x = round(x, 4)
                        poser.pose_controller_l.r_y = round(y, 4)
                        poser.pose_controller_l.r_z = round(z, 4)
                        poser.pose_controller_l.r_w = round(w, 4)
                        
                        poser.pose_controller_r.r_x = round(x, 4)
                        poser.pose_controller_r.r_y = round(y, 4)
                        poser.pose_controller_r.r_z = round(z, 4)
                        poser.pose_controller_r.r_w = round(w, 4)


                    h += 0.01
                except Exception as e :
                    print(f"{e}")
                    break

                await asyncio.sleep(poser.coro_keep_alive["example_thread"][1])

asyncio.run(poser.main())
