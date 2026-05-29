import socket, time, rclpy
from rclpy.Node import Node
from geometry_msgs.msg import Twist
import threading

class Listener(Node):
	def __init__(self):
		super().__init__('listener')
		self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
		threading.Thread(target=self.srv, daemon=True).start()

	def srv(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setscokopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(('0.0.0.0', 10001))
		s.listen(1)
		while rclpy.ok():
			c, i = s.accept()
			if c.recv(1024):
				# forward
				tw = Twist()
				tw .linear.x = 0.2
				self.pub.publish(tw)
				time.sleep(2.0)

				self.pub.publish(Twist())
				c.sendall(b"DONE\n")
			c.close()

def main():
	rclpy.init()
	rclpy.spin(Listener())
