# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
import time
from core.activity_stream import record_event

def observe_process_start(name, args):
    """Log the start of a process."""
    record_event("runtime", "process_start", {"name": name, "args": args})

def observe_process_end(name, status, duration):
    """Log the end of a process."""
    record_event("runtime", "process_end", {"name": name, "status": status, "duration": duration})

def observe_process_exception(name, message):
    """Log an exception during a process."""
    record_event("runtime", "error", {"name": name, "message": message})

def wrap_process_execution(name, func, *args, **kwargs):
    """
    Wrap a process execution to observe its lifecycle.

    :param name: The name of the process.
    :param func: The function to execute.
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    """
    start_time = time.time()
    observe_process_start(name, args)
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        observe_process_end(name, "success", duration)
        return result
    except Exception as e:
        duration = time.time() - start_time
        observe_process_exception(name, str(e))
        observe_process_end(name, "failure", duration)
        raise
