import sys
import math
import cv2 as cv
import rclpy, tf2_ros
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseStamped
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

		self.current_x = 0.0
		self.current_y = 0.0
		self.has_valid_pose = False

		# sync publisher
		self.pose_pub = self.create_publisher(PoseStamped, '/robot_pos', 10)

		# timer part
		self.timer = self.create_timer(0.05, self.sync_pose_time)
		self.get_logger().info("Timer loop running for async get_pos")

	def sync_pose_time(self):
		try:
			transform = self.tf_buffer.lookup_transform(
				FIXED_FRAME,
				ROBOT_FRAME,
				rclpy.time.Time()
			)

			self.current_x = transform.transform.translation.x
			self.current_y = transform.transform.translation.y
			self.has_valid_pose = True

			# publish
			msg = PoseStamped()
			msg.header.frame_id = FIXED_FRAME
			msg.header.stamp = self.get_clock().now().to_msg()

			# position
			msg.pose.position.x = self.current_x
			msg.pose.position.y = self.current_y
			msg.pose.position.z = 0.0

			# orientation 
			msg.pose.orientation.x = transform.transform.rotation.x
			msg.pose.orientation.y = transform.transform.rotation.y
			msg.pose.orientation.z = transform.transform.rotation.z
			msg.pose.orientation.w = transform.transform.rotation.w

			self.pose_pub.publish(msg)

		except TransformException:
			self.has_valid_pose = False

	def get_robot_pose(self):
		if self.has_valid_pose:
			return self.current_x, self.current_y
		else:
			raise RuntimeError("not online to get pos")
