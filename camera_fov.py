import math

def calcdist(angle_of_view, plane_of_view):
    """
    Calculate the distance to the plane of view
    :param angle_of_view: angle of view of the camera
    :param plane_of_view: target plane of view
    :return:
    """
    return round((plane_of_view / 2) / math.tan(math.radians(angle_of_view / 2)),3)

"""
Foosball Table
"""
foosball_table_length = 117
foosball_table_length_with_sidepanels = 146.4
foosball_table_width = 63.4
foosball_table_height = 11

"""
Raspberry pi camera v2
"""
pi_camera_v2_horizontal_fov = 62.2
pi_camera_v2_vertical_fov = 48.8

print("Rasbperry pi camera v2")
print(f"Needed distance to plane: {max(calcdist(pi_camera_v2_horizontal_fov, foosball_table_length), calcdist(pi_camera_v2_vertical_fov, foosball_table_width))}cm")
print(f"Needed distance to plane with sidepanels: {max(calcdist(pi_camera_v2_horizontal_fov, foosball_table_length_with_sidepanels), calcdist(pi_camera_v2_vertical_fov, foosball_table_width))}cm")

"""
Realsense D435
"""
realsense_d435_horizontal_fov = 69.4
realsense_d435_vertical_fov = 42.5
realsense_d435_depth_vertical_fov = 57
realsense_d435_depth_horizontal_fov = 86

print()
print("Realsense D435")
print(f"Needed distance to plane (rgb camera): {max(calcdist(realsense_d435_horizontal_fov, foosball_table_length), calcdist(realsense_d435_vertical_fov, foosball_table_width))}cm")
print(f"Needed distance to plane with sidepanels (rgb camera): {max(calcdist(realsense_d435_horizontal_fov, foosball_table_length_with_sidepanels), calcdist(realsense_d435_vertical_fov, foosball_table_width))}cm")
print(f"Needed distance to plane (depth camera): {max(calcdist(realsense_d435_depth_horizontal_fov, foosball_table_length), calcdist(realsense_d435_depth_vertical_fov, foosball_table_width))}cm")
print(f"Needed distance to plane with sidepanels (depth camera): {max(calcdist(realsense_d435_depth_horizontal_fov, foosball_table_length_with_sidepanels), calcdist(realsense_d435_depth_vertical_fov, foosball_table_width))}cm")


