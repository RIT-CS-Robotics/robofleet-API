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

	def set_pos(self, x, y):
		command = f"SET_POS:{x},{y}\n"
		self.sock.sendall(command.encode("utf-8"))
		response = self.sock.recv(1024).decode("utf-8").strip()
		return response

	def get_pos(self):
		command = f"GET_POS\n"
		self.sock.sendall(command.encode("utf-8"))
		response = self.sock.recv(1024).decode("utf-8").strip()
		if "ERROR" not in response:
			x, y = map(float, response.split(","))
			return x, y
		return response

	def nav_to(self, location):
		command = f"NAV_TO:{location}\n"
		self.sock.sendall(command.encode("utf-8"))
		# block for now
		response = self.sock.recv(1024).decode("utf-8").strip()
		return response

	def move(self, steps):
		command = f"MOVE:{steps}\n"
		self.sock.sendall(command.encode("utf-8"))
		response = self.sock.recv(1024).decode("utf-8")
		return response

	def rotate(self, degrees):
		command = f"ROTATE:{degrees}\n"
		self.sock.sendall(command.encode("utf-8"))
		response = self.sock.recv(1024).decode("utf-8")
		return response
