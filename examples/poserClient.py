"""
this is an example of using virtualreality.templates

to get basic overview of virtualreality.templates.PoserClient run this in your python interpreter:
    help(virtualreality.templates.PoserClient)

to get more info on virtualreality.templates.PoserTemplate run this in your python interpreter:
    help(virtualreality.templates.PoserTemplate)

or visit https://github.com/okawo80085/hobo_vr/blob/master/examples/poserTemplate.py

more examples/references:
    https://github.com/okawo80085/hobo_vr/blob/master/poseTracker.py

"""

import asyncio
import time
import serial

from virtualreality import templates
from virtualreality.server import server
from virtualreality.util import utilz as u

poser = templates.PoserClient()


@poser.thread_register(1 / 100)
async def example_thread():
    while poser.coro_keep_alive["example_thread"][0]:
        try:
            with serial.Serial("COM3", 115200, timeout=1 / 5) as ser2:
                with serial.threaded.ReaderThread(ser2, u.SerialReaderFactory) as protocol:
                    yaw_offset = 0
                    for _ in range(10):
                        protocol.write_line("nut")
                        await asyncio.sleep(1)

                    while poser.coro_keep_alive["example_thread"][0]:
                        try:
                            quat = u.get_numbers_from_text(protocol.last_read)

                            if len(quat) > 0:
                                poser.pose.r_w = round(quat[0], 4)
                                poser.pose.r_x = round(quat[1], 4)
                                poser.pose.r_y = round(quat[2], 4)
                                poser.pose.r_z = round(quat[3], 4)

                                print(poser.pose.r_w, poser.pose.r_x, poser.pose.r_y, poser.pose.r_z, "mag: ", quat[4])

                            await asyncio.sleep(poser.coro_keep_alive["example_thread"][1])

                        except Exception as e:
                            print(f"error: {e}")
                            break

        except Exception as e:
            print(f"serial_listener: {e}")

        await asyncio.sleep(poser.coro_keep_alive["example_thread"][1])


#@poser.thread_register(1, runInDefaultExecutor=True)
#def example_thread2():
#    while poser.coro_keep_alive["example_thread2"][0]:
#        poser.pose["x"] += 0.2
#
#        time.sleep(poser.coro_keep_alive["example_thread2"][1])


asyncio.run(poser.main())
