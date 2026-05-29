import socket
import os

class Robot:
	def __init__(self):
		# self.robot_ip = os.environ.get()
		self.robot_ip = "129.21.65.243" # laptop 3
		self.port = 10001

		# connect socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.robot_ip, self.port))

	def nav_to(self, location):
		command = f"GOTO:{location.upper()}\n"
		self.sock.sendall(command.encode("utf-8"))
		# block for now
		response = self.sock.recv(1024).decode("utf-8")
		return response
