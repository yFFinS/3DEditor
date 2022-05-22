import time
from typing import Callable, Optional


class FuncInfo:
    name: str = ''
    call_count: int = 0
    max_time: float = 0
    tot_time: float = 0
    avg_time: float = 0

    def __init__(self, func: Callable):
        self.name = func.__name__

    def add_call_info(self, time_spent: float):
        self.tot_time += time_spent
        self.max_time = max(self.max_time, time_spent)

        t, avg = self.call_count, self.avg_time
        if t > 0:
            self.avg_time = (time_spent + (t - 1) * avg) / t
        else:
            self.avg_time = time_spent
        self.call_count += 1


class Profiler:
    static_profiler: Optional['Profiler'] = None

    def __init__(self):
        self.__calls: dict[str, FuncInfo] = {}

    @staticmethod
    def init():
        Profiler.static_profiler = Profiler()

    @staticmethod
    def add_call_info(func, time_spent):
        name = func.__name__
        profiler = Profiler.static_profiler
        if name not in profiler.__calls:
            profiler.__calls[name] = FuncInfo(func)

        profiler.__calls[name].add_call_info(time_spent)

    @staticmethod
    def dump(filename: str):
        profiler = Profiler.static_profiler
        names = sorted(profiler.__calls)
        longest_name = ''
        for name in names:
            if len(name) > len(longest_name):
                longest_name = name
        max_call_count = 0
        max_time = 0
        tot_time = 0
        max_avg = 0
        for info in profiler.__calls.values():
            max_call_count = max(max_call_count, info.call_count)
            max_time = max(max_time, info.max_time)
            tot_time = max(tot_time, info.tot_time)
            max_avg = max(max_avg, info.avg_time)
        max_call_count = str(max_call_count)
        max_time = f"{max_time:.2f} ms"
        tot_time = f"{tot_time:.2f} ms"
        max_avg = f"{max_avg:.2f} ms"

        with open(filename, "w+") as f:
            for name in names:
                info = profiler.__calls[name]
                avg_str = f'{info.avg_time:.2f} ms'
                call_str = str(info.call_count)
                max_str = f'{info.max_time:.2f} ms'
                tot_str = f'{info.tot_time:.2f} ms'
                info_str = f"{info.name:<{len(longest_name)}} : " \
                           f"avg_time={avg_str:<{len(max_avg)}}  " \
                           f"call_cnt={call_str:<{len(max_call_count)}}  " \
                           f"max_time={max_str:<{len(max_time)}}  " \
                           f"tot_time={tot_str:<{len(tot_time)}}\n"
                f.write(info_str)


def profile(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        time_spent = time.time() - start
        profiler = Profiler.static_profiler
        if profiler is not None:
            Profiler.static_profiler.add_call_info(func, time_spent * 1000)

        return result

    return wrapper
