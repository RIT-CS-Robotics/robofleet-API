from robot import Robot

print("start connection")
r = Robot()

print("start while loop")
for i in range(3):
	r.move(2)
	r.rotate(0.2)
#print(r.nav_to("RNDLab"))
