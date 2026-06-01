import socket
import roslibpy
import time 
import os

class Robot:
	def __init__(self):
		# self.robot_ip = os.environ.get()
		self.client = roslibpy.Ros(host="129.21.65.243", port 9090) # laptop 3
		self.client.run()

		# connect socket
		self.nav_service = roslibpy.Service(self.client, "/navigate_to_room", "std_srvs/srv/Trigger"
		print("connected to Rosbridge")

	def nav_to(self, location):
		command = f"NAV_TO:{location}\n"
		# self.sock.sendall(command.encode("utf-8"))
		# block for now
		# response = self.sock.recv(1024).decode("utf-8").strip()
		print("sending request to navigate")
		request = roslibpy.ServiceRequest({"message": location_name})

		result = self.nav_service.call(request)
		return result["message"]
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
