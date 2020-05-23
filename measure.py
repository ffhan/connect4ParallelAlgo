import multiprocessing


class Mjerenje:
    def __init__(self):
        try:
            with open('mjerenje.txt', 'r') as file:
                lines = file.readlines()
                self.cpu_count = int(lines[0])
                self.measurements = self._line_to_list(lines[1])
                self.speedup = self._line_to_list(lines[2], float)
                self.efficiency = self._line_to_list(lines[3], float)
        except (FileNotFoundError, IndexError) as e:
            self.cpu_count = multiprocessing.cpu_count()
            self.measurements = [0, ] * 8
            self.speedup = [1, ] * 8
            self.efficiency = [1, ] * 8

    @staticmethod
    def _line_to_list(line, map_func=int):
        return list(map(map_func, line.strip().split(' ')))

    @staticmethod
    def _list_to_line(iterable, map_func=str):
        return ' '.join(map(map_func, iterable)) + '\n'

    def write(self):
        with open('mjerenje.txt', 'w') as file:
            file.write(str(self.cpu_count) + '\n')
            file.write(self._list_to_line(self.measurements))
            float_map = lambda t: '{:.3f}'.format(t)
            file.write(self._list_to_line(self.speedup, float_map))
            file.write(self._list_to_line(self.efficiency, float_map))


def log(func):
    import time

    my_measure = -1
    measure: Mjerenje = Mjerenje()

    def wrapper(self, *args, **kwargs):
        nonlocal my_measure, measure
        if my_measure == -1:
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            my_measure = round((end - start) * 1000)
            this = self.num_of_processes - 1
            measure.measurements[this] = my_measure
            if my_measure != 0:
                measure.speedup[this] = measure.measurements[0] / my_measure
                if self.num_of_processes != 0:
                    measure.efficiency[this] = measure.measurements[0] / (my_measure * self.num_of_processes)
                else:
                    measure.efficiency[this] = 0.0
            else:
                measure.speedup[this] = 0.0
                measure.efficiency = 0.0
            measure.write()
        else:
            result = func(self, *args, **kwargs)
        return result

    return wrapper
