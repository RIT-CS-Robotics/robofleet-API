
import socket, time, rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

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
#			"GO_TO":	self.go_to,
			"NAV_TO":	self.nav_to,
			"GET_POS":	self.get_pos
#			"SET_POS": 	self.set_pos
		}

		threading.Thread(target=self.srv, daemon=True).start()
	"""
	def set_pos(self, location):
		name = str(location).strip()
		try:
			map_x, map_y = map(float, location.split(","))
		except ValueError:
			print(f"Error: Invalid coordinate format")
			return "INVALID SET_POS"

		print(f"Setting initial pose to raw map coordinates: ({map_x:.3f}, {map_y:.3f}")

		# initial pose message
		msg = PoseWithCovarianceStamped()
		msg.header.frame_id = "map"
		msg.header.stamp = self.get_clock().now().to_msg()

		# position
		msg.pose.pose.position.x = map_x
		msg.pose.pose.position.y = map_y
		msg.pose.pose.position.z = 0.0

		# ???
		msg.pose.covariance = [0.0] * 36
		msg.pose.covariance[0] = 0.25
		msg.pose.covariance[7] = 0.25
		msg.pose.covariance[35] = 0.06

		# publish
		self.init_pose_pub.publish(msg)
		return "DONE"
	"""
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
		if steps_val < 0:
			cmd.linear.z = -0.6

		self.pub.publish(cmd)
		time.sleep(abs(deg_val) / 90.0)
		self.pub.publish(Twist())

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

		goal_msg.pose.pose.orientation.x = 0.0
		goal_msg.pose.pose.orientation.y = 0.0
		goal_msg.pose.pose.orientation.z = 0.0

#		self.goal_pub.publish(goal_msg.pose)

		# send action goal synchronously
		print("Submitting goal to Nav2 Server...")
		send_goal_future = self.nav_client.send_goal(goal_msg)

		# if nav2 is mad or not
#		goal_handle = send_goal_future.result()
#		if not send_goal_future.accept:
#			print("Nav2 is mad about the goal... what did you do")
#			return "REJECTED"

#		print("Nav2 happy. Navigating...")

		# future tracking execution
#		result_future = send_goal_future.get_result()

		status = send_goal_future.status


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

	def srv(self):
		# socket stuff (common)
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(('0.0.0.0', 10001))
		s.listen(1)

		while rclpy.ok():
			connect, _ = s.accept()
			try:
				while True:
					raw_data = connect.recv(1024).decode("UTF-8")
					data = raw_data.strip()
					# if string is empty, client dc
					if not data:
						break
					response = "ERROR: failed"
					# use data
					if ":" in data:
						cmd_type, value = data.split(":", 1)
						cmd_type = cmd_type.upper()

						# value (param should be float!!)
						if cmd_type in self.functions:
							response = self.functions[cmd_type](value)
						else:
							response = f"ERROR: unknown command {cmd_type}"
					# cmds without args
					else:
						cmd_type = data.upper()
						if cmd_type in self.functions:
							response = self.functions[cmd_type]()
						else:
							response = f"ERROR: invalid cmd"

					connect.sendall(f"{response}\n".encode('utf-8'))
			except Exception as e:
				print(f"Server exception: {e}")
			finally:
				connect.close()
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
