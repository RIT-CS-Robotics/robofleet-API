from robot import Robot

print("start connection")
r = Robot()

print("getting pose")
pose = r.get_pos()

if (isinstance(pose, tuple)):
	x, y = pose
	print(f"Pose: {x:.3f}, {y:.3f}")
else:
	print(f"Server response error: {pose}")

r.move(1)

pose = r.get_pos()

if (isinstance(pose, tuple)):
	x, y = pose
	print(f"Pose: {x:.3f}, {y:.3f}")
else:
	print(f"Server response error: {pose}")

