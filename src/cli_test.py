import sys
import cv2 as cv
import rclpy
from ament_index_python import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator

PATH = ""
MAP_IMAGE = PATH+"golisano3v5.png"
POINTS_FILE = PATH+"point_database.txt"

RESOLUTION = 0.0388
ORIGIN_X = 0.0
ORIGIN_Y = 0.0


class Point:
    def __init__(self, point, name):
        self.x = point[0]
        self.y = point[1]
        self.name = name

    def get_coords(self):
        return self.x, self.y

    def set_coords(self, point):
        self.x = point[0]
        self.y = point[1]

    def get_name(self):
        return self.name

    def __repr__(self):
        return f"{self.name}\t\t{self.x:.2f} {self.y:.2f}"


class PointDataset:
    def __init__(self, path):
        self.points = []
        self.lookup = {}
        self.load_points(path)

        image = cv.imread(MAP_IMAGE)

        if image is None:
            raise RuntimeError(f"Could not load map image: {MAP_IMAGE}")

        self.image_height = image.shape[0]

    def load_points(self, path):
        with open(path) as F:
            for line in F:
                line = line.strip()

                if not line:
                    continue

                parts = line.split()

                if len(parts) != 3:
                    continue

                name, x, y = parts

                coords = (
                    float(x),
                    float(y)
                )

                point = Point(coords, name)

                self.lookup[name] = point
                self.points.append(point)

    def pixel_to_map(self, px, py):
        map_x = px * RESOLUTION + ORIGIN_X

        map_y = (
            (self.image_height - py)
            * RESOLUTION
            + ORIGIN_Y
        )

        return map_x, map_y


class NavigatorController:

    def __init__(self):
        #rclpy.init()

        self.navigator = BasicNavigator()

        self.goal_pub = self.navigator.create_publisher(
            PoseStamped,
            "/goal_pose",
            10
        )

        print("\nWaiting for Nav2...")
        self.navigator.waitUntilNav2Active()
        print("Nav2 Active")

    def create_goal(self, x, y):
        goal = PoseStamped()

        goal.header.frame_id = "map"

        goal.header.stamp = (
            self.navigator
            .get_clock()
            .now()
            .to_msg()
        )

        goal.pose.position.x = float(x)
        goal.pose.position.y = float(y)
        goal.pose.orientation.w = 1.0

        return goal

    def publish_goal_for_gui(self, goal):
        self.goal_pub.publish(goal)

        rclpy.spin_once(
            self.navigator,
            timeout_sec=0.1
        )

    def follow_waypoints(self, goals):
        self.navigator.followWaypoints(goals)

    def wait_until_complete(self):
        while not self.navigator.isTaskComplete():
            rclpy.spin_once(
                self.navigator,
                timeout_sec=0.1
            )

        result = self.navigator.getResult()

        print(f"\nNavigation Result: {result}")

    def shutdown(self):
        rclpy.shutdown()


def main():
    rclpy.init()

    pd = PointDataset(POINTS_FILE)

    requested_locations = sys.argv[1:]

    if len(requested_locations) == 0:
        print(
            "\nUsage:\n"
            "python3 cli_test.py Office3509 Office3511"
        )
        return

    navigator_controller = NavigatorController()

    goals = []

    for name in requested_locations:

        if name not in pd.lookup:
            print(f"\nNo location named {name}")
            continue

        point = pd.lookup[name]

        px, py = point.get_coords()

        map_x, map_y = pd.pixel_to_map(px, py)

        print(
            f"\n{name}"
            f"\npixel = ({px:.2f}, {py:.2f})"
            f"\nmap    = ({map_x:.2f}, {map_y:.2f})"
        )

        goal = navigator_controller.create_goal(
            map_x,
            map_y
        )

        navigator_controller.publish_goal_for_gui(goal)

        goals.append(goal)

    if len(goals) == 0:
        print("\nNo valid goals")
        navigator_controller.shutdown()
        return

    print("\nSending Waypoints...\n")

    navigator_controller.follow_waypoints(goals)

    navigator_controller.wait_until_complete()

    navigator_controller.shutdown()


if __name__ == "__main__":
    main()
