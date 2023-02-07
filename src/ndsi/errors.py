class CaptureError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class StreamError(CaptureError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message
