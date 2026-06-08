import socket, os, queue, threading, time

class Robot:
	def __init__(self):
		#self.robot_ip = os.environ.get("ROBOT_IP")
		self.robot_ip = "129.21.65.243" # laptop 3
		self.port = 10001

		self._is_traveling = False
		self.block_queue = queue.Queue()
		self.non_block_queue = queue.Queue()

		# connect socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.robot_ip, self.port))
		self.running_program = True

		# start threading
		self.listener_thread = threading.Thread(target=self.listener, daemon=True)
		self.listener_thread.start()

	def listener(self):
		buffer = ""
		while self.running_program:
			try:
				# same bit as listener.py
				data = self.sock.recv(1024).decode("utf-8")
				if not data:
					break

				buffer += data
				while "\n" in buffer:
					line, buffer = buffer.split("\n", 1)
					line = line.strip()

					# empty
					if not line:
						continue

					# end
					if "STATUS" in line:
						self._is_traveling = False
						print("\n Movement finished with",
							" status: ", line)

					elif line == "STARTED":
						self.non_blocking_queue.put(line)

					else:
						self.blocking_queue.put(line)

			except Exception as e:
				print(f"\n Error - robot disconnect.")
				break

	def send_command(self, command):
		self.sock.sendall(command.encode("utf-8"))

	def is_traveling(self):
		return self._is_traveling

	def get_pos(self):
		command = f"GET_POS\n"
		self.send_command(command)

		# wait for bg thread
		try:
			response = self.blocking_queue.get(timeout=1.0)
			if "ERROR" not in response:
				x, y = map(float, response.split(","))
				return x, y
			return response
		except Exception as e:
			print("Error: thread timed out")

	def go_to(self, x, y):
		command = f"GO_TO:{x},{y}\n"
		self._is_traveling = True
		self.send_command(command)

	def nav_to(self, location):
		command = f"NAV_TO:{location}\n"
		self._is_traveling = True
		self.send_command(command)

	def move(self, steps):
		command = f"MOVE:{steps}\n"
		self._is_traveling = True
		self.send_command(command)

	def rotate(self, degrees):
		command = f"ROTATE:{degrees}\n"
		self._is_traveling = True
		self.send_command(command)

	def close(self):
		self.running_program = False
		self.sock.close()
