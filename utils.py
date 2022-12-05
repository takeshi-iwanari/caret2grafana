"""
Utility functions
"""
from __future__ import annotations
import os
import sys
import shutil
import logging
import re
import json
from caret_analyze import Lttng, LttngEventFilter
from caret_analyze.runtime.callback import CallbackBase
from bokeh.plotting import Figure, save
from bokeh.resources import CDN
from bokeh.io import export_png


def create_logger(name, level: int=logging.DEBUG, log_filename: str=None) -> logging.Logger:
    """Create logger"""
    handler_format = logging.Formatter(
        '[%(asctime)s][%(levelname)-7s][%(filename)s:%(lineno)s] %(message)s')
    stream_handler = logging .StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(handler_format)
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(level)
    logger.addHandler(stream_handler)
    if log_filename:
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(handler_format)
        logger.addHandler(file_handler)
    return logger


def read_trace_data(trace_data: str, start_point: float, duration: float,
                    force_conversion=False) -> Lttng:
    """Read LTTng trace data"""
    if start_point > 0 and duration == 0:
        return Lttng(trace_data, force_conversion=force_conversion, event_filters=[
            LttngEventFilter.strip_filter(start_point, None)
        ])
    elif start_point >= 0 and duration > 0:
        return Lttng(trace_data, force_conversion=force_conversion, event_filters=[
            LttngEventFilter.duration_filter(duration, start_point)
        ])
    else:
        return Lttng(trace_data, force_conversion=force_conversion)
