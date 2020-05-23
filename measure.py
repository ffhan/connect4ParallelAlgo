import multiprocessing


class Mjerenje:
    def __init__(self):
        try:
            with open('mjerenje.txt', 'r') as file:
                lines = file.readlines()
                self.cpu_count = int(lines[0])
                self.measurements = self._line_to_list(lines[1])
                self.speedup = self._line_to_list(lines[2])
                self.efficiency = self._line_to_list(lines[3])
        except (FileNotFoundError, IndexError) as e:
            self.cpu_count = multiprocessing.cpu_count()
            self.measurements = [0, ] * 8
            self.speedup = [0, ] * 8
            self.efficiency = [0, ] * 8

    @staticmethod
    def _line_to_list(line):
        return list(map(float, line.strip().split(' ')))

    @staticmethod
    def _list_to_line(iterable):
        return ' '.join(map(str, iterable)) + '\n'

    def write(self):
        with open('mjerenje.txt', 'w') as file:
            file.write(str(self.cpu_count) + '\n')
            file.write(self._list_to_line(self.measurements))
            file.write(self._list_to_line(self.speedup))
            file.write(self._list_to_line(self.efficiency))


def log(func):
    import time

    first_measure = -1
    measure: Mjerenje = Mjerenje()

    def wrapper(self, *args, **kwargs):
        nonlocal first_measure, measure
        if first_measure == -1:
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            first_measure = end - start
            measure.measurements[self.num_of_processes - 1] = first_measure
            measure.write()
        else:
            result = func(self, *args, **kwargs)
        return result

    return wrapper
