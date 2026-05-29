
import socket, time, rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import threading

from cli_test import PointDataset, NavigatorController, POINTS_FILE

class Listener(Node):
	def __init__(self):
		super().__init__('listener')
		self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
		self.pd = PointDataset(POINTS_FILE)
		self.navigator_controller = NavigatorController()
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

		# create goal
		goal = self.navigator_controller.create_goal(map_x, map_y)
		self.navigator_controller.publish_goal_for_gui(goal)

		print("Sending Waypoint...")

		# just one goal per command
		self.navigator_controller.follow_waypoints([goal])
		self.navigator_controller.wait_until_complete()

		# done
		print("success")
		return "DONE"


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
		pass
	finally:
		node.navigator_controller.shutdown()
#		node.destroy_node()
#		rclpy.shutdown()

main()
