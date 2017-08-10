from queue import Queue
import threading
from .epanet2 import EPANET2

class MTEPANET2(object):

    def __init__(self):
        # create thread
        self.qin = Queue(200)
        self.qout = Queue(200)
        # start worker thread
        self.thread = threading.Thread(target=self.worker, daemon=True, args=(self.qin, self.qout))
        self.thread.start()

        self.task = ""

    def worker(self, qin, qout):
        ep = EPANET2()
        while True:
            tt = qin.get()
            try:
                response = getattr(ep, tt["task"])(*tt["args"], **tt["kwargs"])
                qin.task_done()
                qout.put(response)
            except Exception as e:
                qin.task_done()
                qout.put(e)

    def method_wrapper_wrapper(self, task):

        def method_wrapper(*args, **kwargs):
            t = {'task': task, 'args': args, 'kwargs': kwargs}

            self.qin.put(t)
            response = self.qout.get()
            self.qout.task_done()

            if isinstance(response, Exception):
                raise response

            return response

        return method_wrapper

    def __getattr__(self, attr):
        self.task = attr
        return self.method_wrapper_wrapper(attr)
