
import socket, time, rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import Twist
from nav2_msgs.action import NavigateToPose

import threading

from cli_test import PointDataset, POINTS_FILE

class Listener(Node):
	def __init__(self):
		super().__init__('listener')
		self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

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
			"NAV_TO":	self.nav_to
		}

		threading.Thread(target=self.srv, daemon=True).start()

	def move(self, steps):
		print(f"MOVING {steps} steps.")
		cmd = Twist()

		# move speed hardcoded FOR NOW (TEMP)
		cmd.linear.x = 0.2
		if value < 0:
			cmd.linear.x = -0.2

		self.pub.publish(cmd)
		time.sleep(abs(value) * 1.5) # also hardcoded for now
		self.pub.publish(Twist())

	def rotate(self, degrees):
		print(f"TURNING {degrees} degrees.")
		cmd = Twist()

		# turn speed hardcoded FOR NOW (TEMP)
		cmd.angular.z = 0.6
		if value < 0:
			cmd.linear.z = -0.6

		self.pub.publish(cmd)
		time.sleep(abs(value) / 90.0)
		self.pub.publish(Twist())

	def nav_to(self, location):
		name = str(location).strip()

		if name not in self.pd.lookup:
			print(f"No location named {name}")
			return "INVALID"

		# same stuff as cli_test.py
		point = self.pd.lookup[name]
		px, py = point.get_coords()
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

		print("Broken?")

#		self.goal_pub.publish(goal_msg.pose)

		# send action goal synchronously
		print("Submitting goal to Nav2 Server...")
		send_goal_future = self.nav_client.send_goal_async(goal_msg)

		# built in executor engine to wait
		rclpy.spin_until_future_complete(self, send_goal_future)

		# if nav2 is mad or not
		goal_handle = send_goal_future.result()
		if not goal_handle.accepted:
			print("Nav2 is mad about the goal... what did you do")
			return "REJECTED"

		print("Nav2 happy. Navigating...")

		# future tracking execution
		result_future = goal_handle.get_result_async()
		rclpy.spin_until_future_complete(self, result_future)

		status = result_future.result().status


		# success
		if status == 4:
			print("Successfully reached destination.")
			return "DONE"
		else:
			print("Failed to reach destination.")
			return "FAILED"


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

					# use data
					if ":" in data:
						cmd_type, value = data.split(":", 1)
						cmd_type = cmd_type.upper()

						# value (param should be float!!)
						if cmd_type in self.functions:
							self.functions[cmd_type](value)
							connect.sendall(b"DONE\n")
						else:
							connect.sendall(b"ERROR: unknown command")
			except Exception as e:
				pass
			finally:
				connect.close()
def main():
	if not rclpy.ok():
		rclpy.init()
	node = Listener()
	try:
		rclpy.spin(node)
	except KeyboardInterrupt:
		print("ERROR HERE")
	finally:
		node.destroy_node()
		rclpy.shutdown()

main()
