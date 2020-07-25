"""Various VR utilities."""

import queue
import threading
import time
from asyncio.streams import StreamReader
from typing import Sequence, Dict

import cv2
import numpy as np
import serial.threaded
from pykalman import KalmanFilter
from displayarray import read_updates

from itertools import islice, takewhile
import re


def format_str_for_write(input_str: str) -> bytes:
    """Format a string for writing to SteamVR's stream."""
    if len(input_str) < 1:
        return "".encode("utf-8")

    if input_str[-1] != "\n":
        return (input_str + "\n").encode("utf-8")

    return input_str.encode("utf-8")


async def read(reader: StreamReader, read_len: int = 20) -> str:
    """Read one line from reader asynchronously."""
    data = []
    temp = " "
    while "\n" not in temp and temp != "":
        temp = await reader.read(read_len)
        temp = temp.decode("utf-8")
        data.append(temp)
        time.sleep(0)  # allows thread switching

    return "".join(data)


def read2(reader, read_len=20):
    """Read one line from reader asynchronously."""
    data = []
    temp = " "
    while "\n" not in temp and temp != "":
        temp = reader.recv(read_len)
        temp = temp.decode("utf-8")
        data.append(temp)
        time.sleep(0)  # allows thread switching

    return "".join(data)

async def read3(reader: StreamReader, read_len: int = 20) -> str:
    """Read one line from reader asynchronously."""
    data = bytearray()
    temp = b" "
    while b"\n" not in temp and temp != b"":
        temp = await reader.read(read_len)
        data.extend(temp)
        # time.sleep(0)  # allows thread switching

    return data


def rotate_z(points: Dict[str, Dict[str, float]], angle: float):
    """Rotate a set of points around the z axis."""
    sin = np.sin(angle)
    cos = np.cos(angle)

    for key, p in points.items():
        points[key]["x"] = p["x"] * cos - p["y"] * sin
        points[key]["y"] = p["y"] * cos + p["x"] * sin


def rotate_x(points: Dict[str, Dict[str, float]], angle: float):
    """Rotate a set of points around the x axis."""
    sin = np.sin(angle)
    cos = np.cos(angle)

    for key, p in points.items():
        points[key]["y"] = p["y"] * cos - p["z"] * sin
        points[key]["z"] = p["z"] * cos + p["y"] * sin


def rotate_y(points: Dict[str, Dict[str, float]], angle: float):
    """Rotate a set of points around the y axis."""
    sin = np.sin(angle)
    cos = np.cos(angle)

    for key, p in points.items():
        points[key]["x"] = p["x"] * cos - p["z"] * sin
        points[key]["z"] = p["z"] * cos + p["x"] * sin


def rotate(points: Dict[str, Dict[str, float]], angles: Sequence[float]) -> None:
    """
    Rotate a set of points around the x, y, then z axes.

    :param points: a point dictionary, such as: `{"marker 1" : {"x": 0, "y": 0, "z": 0}}`
    :param angles: the degrees to rotate on the x, y, and z axes
    """
    if angles[0] != 0:
        rotate_x(points, angles[0])

    if angles[1] != 0:
        rotate_y(points, angles[1])

    if angles[2] != 0:
        rotate_z(points, angles[2])


def translate(points: Dict[str, Dict[str, float]], offsets: Sequence[float]) -> None:
    """
    Translate a set of points along the x, y, then z axes.

    :param points: a point dictionary, such as: `{"marker 1" : {"x": 0, "y": 0, "z": 0}}`
    :param offsets: the distance to translate on the x, y, and z axes
    """
    for key, p in points.items():
        points[key]["x"] += offsets[0]
        points[key]["y"] += offsets[1]
        points[key]["z"] += offsets[2]


def strings_share_characters(str1: str, str2: str) -> bool:
    """Determine if two strings share any characters."""
    for i in str2:
        if i in str1:
            return True

    return False


def get_numbers_from_text(text, separator="\t"):
    """Get a list of number from a string of numbers seperated by :separator:[default: "\t"]."""
    try:
        if isinstance(text, bytearray) or isinstance(text, bytes):
            text = text.decode("utf-8")

        if strings_share_characters(text.lower(), "qwrtyuiopsasdfghjklzxcvbnm><*[]{}()") or len(text) == 0:
            return []

        return [float(i) for i in text.split(separator)]

    except Exception as e:
        print(f"get_numbers_from_text: {repr(e)} {repr(text)}")

        return []

def get_pose_struct_from_text(text):
    '''returns struct from :text:, :text: has to be styled so that it matches this regex: ([hct][0-9]+[ ]{0,1})+'''
    res = re.search('([hct][0-9]+[ ]{0,1})+', text)
    if res != None:
        if res.group(0) == text:
            return tuple(i[0] for i in text.split(' ')), tuple(int(i[1:]) for i in text.split(' '))
    return (), ()

def parse_poses_from_packet(packet, struct):
    '''parses all poses from a :packet:, provided a packet :struct:'''
    it = iter(packet)
    return [tuple(islice(it, 0, i)) for i in struct]

def get_poses_shape(poses):
    '''returns a shape of :poses: parsed by parse_poses_from_packet'''
    return tuple(len(i) for i in poses)

def has_nan_in_pose(pose):
    """Determine if any numbers in pose are invalid."""
    for key in ["x", "y", "z"]:
        if np.isnan(pose[key]) or np.isinf(pose[key]):
            return True

    return False


class LazyKalman:
    """
    no docs... too bad.

    But then, SimLeek added some.

    example usage:
        t = LazyKalman([1, 2, 3], np.eye(3), np.eye(3)) # init filter

        for i in range(10):
            print (t.apply([5+i, 6+i, 7+i])) # apply and update filter
    """

    def __init__(self, init_state, transition_matrix, observation_matrix, n_iter=5, train_size=15):
        """
        Create the Kalman filter.

        :param init_state: Initial state of the Kalman filter. Should be equal to first element in first_train_batch.
        :param transition_matrix: adjacency matrix representing state transition from t to t+1 for any time t
                                  Example: http://campar.in.tum.de/Chair/KalmanFilter
                                  Most likely, this will be an NxN eye matrix the where N is the number of variables
                                  being estimated
        :param observation_matrix: translation matrix from measurement coordinate system to desired coordinate system
                                   See: https://dsp.stackexchange.com/a/27488
                                   Most likely, this will be an NxN eye matrix the where N is the number of variables
                                   being estimated
        :param n_iter: Number of times to repeat the parameter estimation function (estimates noise)
        """
        init_state = np.array(init_state)
        transition_matrix = np.array(transition_matrix)
        observation_matrix = np.array(observation_matrix)

        self._expected_shape = init_state.shape

        self._filter = KalmanFilter(
            transition_matrices=transition_matrix,
            observation_matrices=observation_matrix,
            initial_state_mean=init_state,
        )

        self._calibration_countdown = 0
        self._calibration_observations = []
        self._em_iter = n_iter

        self.calibrate(train_size, n_iter)

        self._x_now = np.zeros(3)
        self._p_now = np.zeros(3)

    def apply(self, obz):
        """Apply the Kalman filter against the observation obz."""
        # Todo: automatically start a calibration routine if everything is at rest for long enough,
        #  or if the user leaves, or if there is enough error. Also, add some UI calibrate button, save, and load.
        obz = np.array(obz)

        assert obz.shape == self._expected_shape, "shape miss match"

        self._x_now, self._p_now = self._filter.filter_update(
            filtered_state_mean=self._x_now, filtered_state_covariance=self._p_now, observation=obz,
        )

        if self._calibration_countdown:
            self._calibration_observations.append(obz)
            self._calibration_countdown -= 1
            if self._calibration_countdown == 0:
                self._run_calibration()
        return self._x_now

    def _run_calibration(self):
        """Update the Kalman filter so that noise matrices are more accurate."""
        t_start = time.time()
        self._filter = self._filter.em(self._calibration_observations, n_iter=self._em_iter)
        print(f" kalman filter calibrated, took {time.time() - t_start}s")
        f_means, f_covars = self._filter.filter(self._calibration_observations)
        self._x_now = f_means[-1, :]
        self._p_now = f_covars[-1, :]
        self._calibration_observations = []

    def calibrate(self, observations=100000, em_iter=10):
        """
        Start the calibration routine.

        :param observations: Number of observations before calibration runs.
        :param em_iter: number of times calibration runs over all observations.
        """
        self._calibration_countdown = observations
        self._em_iter = em_iter


class SerialReaderFactory(serial.threaded.LineReader):
    """
    A protocol factory for serial.threaded.ReaderThread.

    self.lastRead should be read only, if you need to modify it make a copy

    usage:
        with serial.threaded.ReaderThread(serial_instance, SerialReaderFactory) as protocol:
            protocol.lastRead # contains the last incoming message from serial
            protocol.write_line(single_line_text) # used to write a single line to serial
    """

    def __init__(self):
        """Create the SerialReaderFactory."""
        super().__init__()
        self._last_read = ""

    @property
    def last_read(self):
        """Get the readonly last read."""
        return self._last_read

    def handle_line(self, data):
        """Store the latest line in last_read."""
        self._last_read = data
        # print (f'cSerialReader: data received: {repr(data)}')

    def connection_lost(self, exc):
        """Notify the user that the connection was lost."""
        print(f"SerialReaderFactory: port {repr(self.transport.serial.port)} closed {repr(exc)}")


class BlobTracker(threading.Thread):
    """
    Tracks color blobs in 3D space.

    all tracking is done in a separate thread, so use this class in context manager

    self.start() - starts tracking thread
    self.close() - stops tracking thread

    self.get_poses() - gets latest tracker poses
    """

    def __init__(
        self, cam_index=0, *, focal_length_px=490, ball_radius_cm=2, color_masks={},
    ):
        """
        Create a blob tracker.

        example usage:
        >>> tracker = BlobTracker(color_masks={
        ...         'tracker1':{
        ...             'h':(98, 10),
        ...             's':(200, 55),
        ...             'v':(250, 32)
        ...         },
        ... })

        >>> with tracker:
        ...     for _ in range(3):
        ...         poses = tracker.get_poses() # gets latest poses for the trackers
        ...         print (poses)
        ...         time.sleep(1/60) # some delay, doesn't affect the tracking
        {'tracker1': {'x': 0, 'y': 0, 'z': 0}}
        {'tracker1': {'x': 0, 'y': 0, 'z': 0}}
        {'tracker1': {'x': 0, 'y': 0, 'z': 0}}

        :param cam_index: index of the camera that will be used to track the blobs
        :param focal_length_px: focal length in pixels
        :param ball_radius_cm: the radius of the ball to be tracked in cm
        :param color_masks: color mask parameters, in opencv hsv color space, for color detection
        """
        super().__init__()
        self._vs = read_updates(cam_index)

        time.sleep(2)

        self.camera_focal_length = focal_length_px
        self.BALL_RADIUS_CM = ball_radius_cm
        self.cam_index = cam_index

        self.last_frame = None
        self.time_of_last_frame = -1

        frame, self.can_track = self._try_get_frame()

        if not self.can_track:
            self._vs.end()
            self._vs = None
            raise RuntimeError('invalid video source')


        self.frame_height, self.frame_width, _ = frame.shape if self.can_track else (0, 0, 0)

        self.markerMasks = color_masks

        self.poses = {}
        self.blobs = {}

        self.kalmanTrainSize = 15

        self.kalmanFilterz: Dict[str, LazyKalman] = {}
        self.kalmanWasInited = {}

        self.kalmanFilterz2: Dict[str, LazyKalman] = {}
        self.kalmanWasInited2 = {}

        for i in self.markerMasks:
            self.poses[i] = {"x": 0, "y": 0, "z": 0}
            self.blobs[i] = None

            self.kalmanFilterz[i] = None
            self.kalmanWasInited[i] = False

            self.kalmanFilterz2[i] = None
            self.kalmanWasInited2[i] = False

        # -------------------threading related------------------------

        self.alive = True
        self._lock = threading.Lock()
        self.daemon = False
        self.pose_que = queue.Queue()

    def _try_get_frame(self):
        self._vs.update()
        try:
            frame = self._vs.frames[str(self.cam_index)][0]
            can_track = True
            if frame is not self.last_frame:
                self.time_of_last_frame = time.time()
        except Exception as e:
            print("_try_get_frame() failed with:", repr(e), self._vs.frames)
            frame = None
            can_track = False
        return frame, can_track

    def stop(self):
        """Stop the blob tracking thread."""
        self.alive = False
        self.can_track = False
        self.join(4)

    def run(self):
        """Run the main blob tracking thread."""
        try:
            _, self.can_track = self._try_get_frame()

            if not self.can_track:
                raise RuntimeError("video source already expired")

        except Exception as e:
            print(f"failed to start thread, video source expired?: {repr(e)}")
            self.alive = False
            return

        while self.alive and self.can_track:
            try:
                self.find_blobs_in_frame()
                self.solve_blob_poses()
                # rotate(self.poses, self.offsets)

                if not self.pose_que.empty():
                    try:
                        self.pose_que.get_nowait()

                    except queue.Empty:
                        pass

                self.pose_que.put(self.poses.copy())

                if not self.can_track:
                    break

            except Exception as e:
                print(f"tracking failed: {repr(e)}")
                break

        self.alive = False
        self.can_track = False

    def get_poses(self) -> Dict[str, Dict[str, float]]:
        """Get the least recent set of poses."""
        if self.can_track and self.alive:
            return self.pose_que.get()
        else:
            raise RuntimeError("tracking loop already finished")

    def find_blobs_in_frame(self):
        """Get a frame from the camera and find all the blobs in it."""
        if self.alive:
            frame, self.can_track = self._try_get_frame()

            for key, mask_range in self.markerMasks.items():
                hc, hr = mask_range["h"]

                sc, sr = mask_range["s"]

                vc, vr = mask_range["v"]

                color_high = [hc + hr, sc + sr, vc + vr]
                color_low = [hc - hr, sc - sr, vc - vr]

                if self.can_track:
                    blurred = cv2.GaussianBlur(frame, (3, 3), 0)

                    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

                    mask = cv2.inRange(hsv, tuple(color_low), tuple(color_high))

                    temp = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if len(temp) == 3:
                        _, cnts, hr = temp

                    else:
                        cnts, hr = temp

                    if len(cnts) > 0:
                        c = max(cnts, key=cv2.contourArea)
                        self.blobs[key] = c if len(c) >= 5 and cv2.contourArea(c) > 10 else None

    def solve_blob_poses(self):
        """Solve for and set the poses of all blobs visible by the camera."""
        for key, blob in self.blobs.items():
            if blob is not None:
                elip = cv2.fitEllipse(blob)

                x, y = elip[0]
                w, h = elip[1]

                if not self.kalmanWasInited2[key]:
                    self.kalmanFilterz2[key] = LazyKalman([x, y, w], np.eye(3), np.eye(3))
                    self.kalmanWasInited2[key] = True

                else:
                    x, y, w = self.kalmanFilterz2[key].apply([x, y, w])

                f_px = self.camera_focal_length
                x_px = x
                y_px = y
                a_px = w / 2

                x_px -= self.frame_width / 2
                y_px = self.frame_height / 2 - y_px

                l_px = np.sqrt(x_px ** 2 + y_px ** 2)

                k = l_px / f_px

                j = (l_px + a_px) / f_px

                l = (j - k) / (1 + j * k)

                d_cm = self.BALL_RADIUS_CM * np.sqrt(1 + l ** 2) / l

                fl = f_px / l_px

                z_cm = d_cm * fl / np.sqrt(1 + fl ** 2)

                l_cm = z_cm * k

                x_cm = l_cm * x_px / l_px
                y_cm = l_cm * y_px / l_px

                self.poses[key]["x"] = x_cm / 100
                self.poses[key]["y"] = y_cm / 100
                self.poses[key]["z"] = z_cm / 100

                # self._translate()

                if not has_nan_in_pose(self.poses[key]):
                    if not self.kalmanWasInited[key]:
                        self.kalmanFilterz[key] = LazyKalman(
                            [self.poses[key]["x"], self.poses[key]["y"], self.poses[key]["z"],], np.eye(3), np.eye(3)
                        )
                        self.kalmanWasInited[key] = True
                    else:
                        self.poses[key]["x"], self.poses[key]["y"], self.poses[key]["z"] = self.kalmanFilterz[
                            key
                        ].apply([self.poses[key]["x"], self.poses[key]["y"], self.poses[key]["z"]])

    def close(self):
        """Close the blob tracker thread."""
        with self._lock:
            self.stop()

            if self._vs is not None:
                self._vs.end()
                self._vs = None

    def __enter__(self):
        self.start()
        if not self.alive:
            self.close()
            raise RuntimeError("video source already expired")

        return self

    def __exit__(self, *exc):
        self.close()
