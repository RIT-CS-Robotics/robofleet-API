# robofleet-API - How to Run (Laptop 3 only)
ros2 launch robofleet_bringup robofleet.launch.xml OR ros2 launch p3dx_gazebo golisano.launch.xml
\nros2 run rviz2 rviz2
\n{for navigation} ros2 launch p3dx_navigation amcl_fleet.launch.py use_sime_time:=true

cd robofleet-API/src
python3 listener.py
python3 run_test.py
