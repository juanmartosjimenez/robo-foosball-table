import multiprocessing

class ProcessManager:
    def __init__(self):
        self.queue_from_camera = multiprocessing.Queue()
        self.queue_from_motors = multiprocessing.Queue()
        self.queue_to_camera = multiprocessing.Queue()
        self.queue_to_motors = multiprocessing.Queue()
        self.queue_to_tkinter_frontend = multiprocessing.Queue()
        self.queue_from_tkinter_frontend = multiprocessing.Queue()

        self.frontend: Optional[Frontend] = None
        self.publisher = Publisher(
            events=[FrontendEvent.ENCODER_VALS, FrontendEvent.CURRENT_BALL_POS, FrontendEvent.PREDICTED_BALL_POS,
                    FrontendEvent.ERROR])
        self.active_threads = []
        self.stop_flag = multiprocessing.Event()
        self.stop_flag.set()