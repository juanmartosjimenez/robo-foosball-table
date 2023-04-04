class BallPrediction:
    def __init__(self, x_pixels, y_pixels, rate, queue_from_camera, target_x_pixel):
        # Total number of x pixels in the playing field.
        self.x_pixels = x_pixels
        # Total number of y pixels in the playing field.
        self.y_pixels = y_pixels
        # Rate at which new ball positions are added. Should be 60fps.
        self.rate = rate
        # Damping factor. Rate at which the ball slows down.
        self.damping = 0.9
        # Threshold speed. Speed at which prediction of ball is no longer taking into account but rather the current
        # ball position.
        self.threshold = 0.1
        # Restitution factor. Rate at which the ball bounces off the walls.
        self.restitution = 0.5
        # Buffer to store current ball pixels.
        self.buffer = []
        # Predicted ball pixels.
        self.predicted = []
        # Queue used to send out
        self.queue_from_camera = queue_from_camera
        # Target x pixel position. Position of the goalie bar.
        self.target_x_pixel = target_x_pixel

    def add_new(self, x_pixel, y_pixel):
        self.buffer.insert(0, self.queue_from_camera.get())

    def predict(self):
        pass

