CTRL_MODE                 = "MODE"
CTRL_TIME                 = "TIME"
CTRL_PRESSURE             = "PRESSURE"
CTRL_STREAM_ADDR          = "STREAM_ADDR"
CTRL_STREAM_PORT          = "STREAM_PORT"
CTRL_STATUS               = "STATUS"
CTRL_REC_NAME             = "REC_NAME"
CTRL_REC_TIME             = "REC_TIME"
CTRL_REC_SIZE             = "REC_SIZE"
CTRL_BANDWIDTH_ESTIMATE   = "BANDWIDTH_ESTIMATE"

__all__ = []
for name in dir():
    if name.startswith('CTRL_'):
        __all__.append(name)