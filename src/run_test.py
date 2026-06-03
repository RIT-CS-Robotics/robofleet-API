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

r.nav_to("Office3511")

i = 1
while i < 2:
	pose = r.get_pos()
	r.move(1)
	if (isinstance(pose, tuple)):
		x, y = pose
		print(f"Pose: {x:.3f}, {y:.3f}")
	else:
		print(f"Server response error: {pose}")
	i = i + 1
