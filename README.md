# robofleet-API - How to Run 

ros2 launch robofleet_bringup robofleet.launch.xml OR ros2 launch p3dx_gazebo golisano.launch.xml  
ros2 run rviz2 rviz2  
{for navigation} ros2 launch p3dx_navigation amcl_fleet.launch.py use_sime_time:=true  
  
cd robofleet-API/src  
python3 listener.py  --> laptop1
python3 run_test.py  

# to run from laptop 3  
adjust run_test.py to import from robot_test, not robot
python3 listener2.py
python3 run_test.py  

# web server
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
