import asyncio
import time
import sys
import numpy as np
import pyrr
import logging

from virtualreality import templates
from virtualreality.util import utilz as u

logging.basicConfig(level=logging.DEBUG, filename='server_ping.log', format="%(levelname)s - %(message)s")

poser = templates.PoserClient(send_delay=1/50)

#number of pose pings to server for testing only
NUM_PINGS = 10

@poser.thread_register(1/50)
async def pose_ping():
    i=0
    while poser.coro_keep_alive["pose_ping"][0]:
        print(i, NUM_PINGS)
        try:
            logging.debug("===================================")
            logging.debug("Ping %d/%d:", i, NUM_PINGS)

            logging.debug("DummyData:")
            logging.debug(f"pose[\"x\"]) = {np.sin(i)}")
            logging.debug(f"pose[\"y\"]) = {np.cos(i)}")
            logging.debug(f"pose[\"z\"]) = {np.cos(i)}")

            poser.pose["x"] = round(np.sin(i), 4)
            poser.pose["y"] = round(np.cos(i), 4)
            poser.pose["z"] = round(np.cos(i), 4)

            poser.pose_controller_l["x"] = round(np.sin(i), 4)
            poser.pose_controller_l["y"] = round(np.cos(i), 4)
            poser.pose_controller_l["z"] = round(np.cos(i), 4)

            poser.pose_controller_r["x"] = round(np.sin(i), 4)
            poser.pose_controller_r["y"] = round(np.cos(i), 4)
            poser.pose_controller_r["z"] = round(np.cos(i), 4)

            i += 1
        
        except Exception as e:
            logging.debug(f"{e}")
            poser.coro_keep_alive["pose_ping"][0] = False
            sys.exit(1)

        logging.debug("Successfully updated pose at %f\n\n", time.time())

        if(i < NUM_PINGS):
            await asyncio.sleep(poser.coro_keep_alive["pose_ping"][1])
        else :
            poser.coro_keep_alive["pose_ping"][0] = False
            return

asyncio.run(poser.main())
