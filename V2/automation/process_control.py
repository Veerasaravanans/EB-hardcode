import psutil
import logging

logger = logging.getLogger(__name__)

def get_running_processes():
    processes = set()
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                processes.add((proc.info['pid'], proc.info['name'].lower()))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Error getting running processes: {e}")
    return processes

def get_new_processes(before_processes):
    current = get_running_processes()
    new = current - before_processes
    return list(new)

def close_app_by_name(process_names):
    killed = False
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if any(pname.lower() in name.lower() for pname in process_names):
                proc.terminate()
                logger.info(f"Terminated {name} (PID {proc.pid})")
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed

def close_app_by_pid(pids):
    killed = False
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            logger.info(f"Terminated process PID {pid}")
            killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed
