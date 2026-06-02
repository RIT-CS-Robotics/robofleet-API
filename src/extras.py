import sys
import math
import cv2 as cv
import rclpy, tf2_ros
from rclpy.node import Node
from tf2_ros import TransformException

RESOLUTION = 0.388
ORIGIN_X = 0.0
ORIGIN_Y = 0.0

FIXED_FRAME = "map"
ROBOT_FRAME = "base_link"

MAP_IMAGE = "golisano3v5.png"

class PointDataset:
    def __init__(self, path):
        self.lookup = {}

        image = cv.imread(MAP_IMAGE)

        if image is None:
            raise RuntimeError(f"Could not load map image: {MAP_IMAGE}")

        self.image_height = image.shape[0]
        self.image_width = image.shape[1]

        self.load_points(path)

    def load_points(self, path):
        with open(path) as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                parts = line.split()

                if len(parts) != 3:
                    continue

                name, x, y = parts
                self.lookup[name] = (float(x), float(y))

    def map_to_pixel(self, map_x, map_y):
        pixel_x = (map_x - ORIGIN_X) / RESOLUTION
        pixel_y = self.image_height - ((map_y - ORIGIN_Y) / RESOLUTION)
        return pixel_x, pixel_y

    def pixel_to_map(self, pixel_x, pixel_y):
        map_x = (pixel_x * RESOLUTION) + ORIGIN_X
        map_y = ((self.image_height - pixel_y) * RESOLUTION) + ORIGIN_Y
        return map_x, map_y

class PoseReader(Node):
    def __init__(self):
        super().__init__("correction_logger")

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(
            self.tf_buffer,
            self
        )

    def get_robot_pose(self):
        for i in range(10):
            try:
                transform = self.tf_buffer.lookup_transform(
                    FIXED_FRAME,
                    ROBOT_FRAME,
                    rclpy.time.Time()
                )

                x = transform.transform.translation.x
                y = transform.transform.translation.y

                return x, y

            except TransformException:
                time.sleep(0.1)

        raise RuntimeError("Transform between map and base link is unavailable.")

