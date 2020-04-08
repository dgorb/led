import threading

# Thread with stop
class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()
        self._wait = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def wait(self):
        self._wait.set()

    def cont(self):
        self._wait.clear()

    def waiting(self):
        return self._wait.isSet()

class Controller:
    def __init__(self):
        # 1 thread for each pin (RGB), + log for dynamic logging?
        # Maybe log should be a separate thing with its own thread
        self.threads = dict()

    def get_thread(self, name):
        return self.threads[name]

    def add(self, name, func, *args):
        thread = Thread(target=func, args=args)
        if name not in ('r', 'g', 'b', 'log'):
            raise Exception(f"unsupported thread name: {name}")
        self.threads[name] = thread

    def start(self, name):
        if not name in self.threads:
            raise Exception(f"no thread '{name}' found")
        self.threads[name].start()

    def start_all(self):
        for n, t in self.threads.items():
            if t.is_alive():
                raise Warning(f"thread '{n}' is already running")
            t.start()

    def stop(self, name):
        if not name in self.threads:
            raise Exception(f"no thread '{name}' found")
        self.threads[name].stop()

    def stop_all(self):
        for n, t in self.threads.items():
            if t.stopped():
                raise Warning(f"thread '{n}' is already stopped")
            t.stop()

    def waiting(self, name):
        return self.threads[name].waiting()

    def cont_all(self):
        for t in self.threads.values():
            t.cont()

    def all_waiting(self):
        return all([t.waiting() == True for t in self.threads.values()])

    # True if at least one thread is alive
    def alive(self):
        for n, t in self.threads.items():
            # FIXME: log should be somewhere else
            if n == 'log':
                continue
            if not t.stopped():
                return True
        return False
