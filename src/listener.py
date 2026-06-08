import socket, time, rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from ament_index_python import get_package_share_directory
from geometry_msgs.msg import Twist, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose

import threading

from extras import PointDataset, PoseReader

class Listener(Node):
	def __init__(self):
		super().__init__('listener')
		self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
		self.init_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
		self.pose_reader = PoseReader()
		self.current_client = None

		# previously CLI_TEST imports
		PATH = "" # adjust as needed
		POINTS_FILE = PATH+"point_database.txt"
		self.pd = PointDataset(POINTS_FILE)

		# native ros2 ActionClient targeting nav2 server
		self.get_logger().info("Waiting for nav2 action server...")
		self.nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

		# wait for nav2 server (block)
		self.nav_client.wait_for_server()
		self.get_logger().info("Nav2 ActionServer ready.")

		# all possible commands
		self.functions = {
			"MOVE":		self.move,
			"ROTATE":	self.rotate,
			"GO_TO":	self.go_to,
			"NAV_TO":	self.nav_to,
			"GET_POS":	self.get_pos
#			"SET_POS": 	self.set_pos
		}

		threading.Thread(target=self.srv, daemon=True).start()

	def move(self, steps):
		print(f"MOVING {steps} steps.")
		cmd = Twist()
		steps_val = float(steps)
		# move speed hardcoded FOR NOW (TEMP)
		cmd.linear.x = 0.2
		if steps_val < 0:
			cmd.linear.x = -0.2

		self.pub.publish(cmd)
		time.sleep(abs(steps_val) * 1.5) # also hardcoded for now
		self.pub.publish(Twist())

	def rotate(self, degrees):
		print(f"TURNING {degrees} degrees.")
		cmd = Twist()
		deg_val = float(degrees)

		# turn speed hardcoded FOR NOW (TEMP)
		cmd.angular.z = 0.6
		if deg_val < 0:
			cmd.linear.z = -0.6

		self.pub.publish(cmd)
		time.sleep(abs(deg_val) / 90.0)
		self.pub.publish(Twist())

	def go_to(self, coordinates):
		coord_str = str(coordinates).strip()
		x_str, y_str = coord_str.split(",")

		x = float(x_str)
		y = float(y_str)

		map_x, map_y = self.pd.pixel_to_map(x, y)
		print(
			f" \n Sending Robot to ({x:.2f}, {y:.2f}),"
			f" \n Map = ({map_x:.2f}, {map_y:.2f})"
		)

		# construct goal message
		goal_msg = NavigateToPose.Goal()
		goal_msg.pose.header.frame_id = "map"
		goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
		goal_msg.pose.pose.position.x = float(map_x)
		goal_msg.pose.pose.position.y = float(map_y)
		goal_msg.pose.pose.orientation.w = 1.0 # FORWARD FACING (TEMP)

		# send goal to Nav2
		print("Submitting goal to Nav2 Server...")
		send_goal_future = self.nav_client.send_goal_async(goal_msg)

		while rclpy.ok() and not send_goal_future.done():
			time.sleep(0.05)

		# if nav2 is mad or not
		goal_handle = send_goal_future.result()
		if not goal_handle.accepted:
			print("Nav2 is mad about the goal... what did you do")
			return "REJECTED"

		print("Nav2 happy. Navigating...")

		# future tracking execution
		result_future = goal_handle.get_result_async()

		while rclpy.ok() and not result_future.done():
			time.sleep(0.05)

		status = result_future.result().status

		# success
		if status == 4:
			print("Successfully reached destination.")
			return "DONE"
		else:
			print("Failed to reach destination.")
			return "FAILED"


	def nav_to(self, location):
		name = str(location).strip()

		if name not in self.pd.lookup:
			print(f"No location named {name}")
			return "INVALID"

		# same stuff as cli_test.py
		point = self.pd.lookup[name]
		px, py = point
		map_x, map_y = self.pd.pixel_to_map(px, py)

		print(
			f"\n Sending Robot to: {name}"
			f"\n Pixel = ({px:.2f}, {py: .2f})"
		)

		# new: construct goal msg
		goal_msg = NavigateToPose.Goal()
		goal_msg.pose.header.frame_id = "map"
		goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
		goal_msg.pose.pose.position.x = float(map_x)
		goal_msg.pose.pose.position.y = float(map_y)
		goal_msg.pose.pose.orientation.w = 1.0 # FORWARD FACING (TEMP)

#		goal_msg.pose.pose.orientation.x = 0.0
#		goal_msg.pose.pose.orientation.y = 0.0
#		goal_msg.pose.pose.orientation.z = 0.0

#		self.goal_pub.publish(goal_msg.pose)

		# send action goal synchronously
		print("Submitting goal to Nav2 Server...")
		send_goal_future = self.nav_client.send_goal_async(goal_msg)

		#rclpy.spin_until_future_complete(self, send_goal_future)

		while rclpy.ok() and not send_goal_future.done():
			time.sleep(0.05)

		# if nav2 is mad or not
		goal_handle = send_goal_future.result()
		if not goal_handle.accepted:
			print("Nav2 is mad about the goal... what did you do")
			return "REJECTED"

		print("Nav2 happy. Navigating...")

		# future tracking execution
		result_future = goal_handle.get_result_async()
#		rclpy.spin_until_future_complete(self, result_future)
		while rclpy.ok() and not result_future.done():
			time.sleep(0.05)
		status = result_future.result().status


		# success
		if status == 4:
			print("Successfully reached destination.")
			return "DONE"
		else:
			print("Failed to reach destination.")
			return "FAILED"


	def get_pos(self):
		"""
		Get (x, y) coordinates of robot's location.
		"""

		print("Getting current robot position...")
		try:
			x, y = self.pose_reader.get_robot_pose()
			resp = f"{x:.3f},{y:.3f}"
			print(resp)
			return resp
		except Exception as e:
			return "ERROR: Cannot get current pose"

	def run_non_blocking_action(self, func, value):
		result = func(value)
		if self.current_client:
			try:
				self.current_client.sendall(f"STATUS: {result}\n".encode("utf-8"))
			except Exception as e:
				print("Uh oh, {e}")

	def srv(self):
		# socket stuff (common)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(('0.0.0.0', 10001))
		s.listen(1)

		while rclpy.ok():
			connect, _ = s.accept()
			buffer = ""
			try:
				while True:
					raw_data = connect.recv(1024).decode("UTF-8")
					# if string is empty, client dc
					if not raw_data:
						break
					buffer += raw_data

					# all commands sent over
					while "\n" in buffer:
						data, buffer = buffer.split("\n", 1)
						data = data.strip()

						response = "ERROR: failed"
						cmd_type = ""
						value = None

						# use data
						if ":" in data:
							cmd_type, value = data.split(":", 1)
							cmd_type = cmd_type.upper()

						# cmds without args
						else:
							cmd_type = data.upper()
						if cmd_type in self.functions:
							non_blocking = ["MOVE", "ROTATE", "GO_TO", "NAV_TO"]
							if cmd_type in non_blocking:
								threading.Thread(
									target=self.run_non_blocking_action,
									args=(self.functions[cmd_type], value),
									daemon=True
								).start()
								response = "STARTED {cmd_type}"
							else:
								if value:
									response = self.functions[cmd_type](value)
								else:
									response = self.functions[cmd_type]()

						else:
							response = f"ERROR: invalid cmd"

						connect.sendall(f"{response}\n".encode('utf-8'))
			except Exception as e:
				print(f"Server exception: {e}")
			finally:
				if self.current_client is not None:
					try:
						self.current_client.close()
						self.current_client = None
					except Exception as e:
						print(f"server exception: {e}")

def main():
	if not rclpy.ok():
		rclpy.init()
	node = Listener()

	executor = MultiThreadedExecutor()
	executor.add_node(node)
	executor.add_node(node.pose_reader)

	try:
		executor.spin()
	except KeyboardInterrupt:
		print("ERROR HERE")
	finally:
		node.destroy_node()
		rclpy.shutdown()

main()
