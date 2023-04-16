
BALL_POSITION_DIR = "data_visualization/data/"
def ball_writer(filename, x_pixel, y_pixel):
    # Writes current ball position to file.
    if x_pixel is None or y_pixel is None:
        return
    x_pixel, y_pixel = self.__convert_to_playing_field_pixel(x_pixel, y_pixel)
    with open(BALL_POSITION_FILE, "w") as f:
        f.write(f"{str(x_pixel)},{str(y_pixel)}\n")