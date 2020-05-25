import multiprocessing


class Mjerenje:
    """
    Object representing mjerenje.txt file and it's operation (parsing/writing to it)
    """

    def __init__(self):
        try:  # parse the file
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
    def _line_to_list(line, map_func=int) -> list:
        """
        Parse line to a list.

        :param line: line from the file
        :param map_func: mapping function for individual values in the line
        :return: list object
        """
        return list(map(map_func, line.strip().split(' ')))

    @staticmethod
    def _list_to_line(iterable, map_func=str) -> str:
        """
        Marshal list to a string (representing one line in a file).

        :param iterable: iterable object
        :param map_func: mapping function for values in a list
        :return: string object
        """
        return ' '.join(map(map_func, iterable)) + '\n'

    def write(self):
        """
        Write the current Mjerenje state to a file.
        :return:
        """
        with open('mjerenje.txt', 'w') as file:
            file.write(str(self.cpu_count) + '\n')
            file.write(self._list_to_line(self.measurements))
            float_map = lambda t: '{:.3f}'.format(t)
            file.write(self._list_to_line(self.speedup, float_map))
            file.write(self._list_to_line(self.efficiency, float_map))


def log(func):
    """
    Annotation used to measure execution of a method only for its' first run.
    Method can be used only for classes that contain field "num_of_processes".

    :param func: function to be wrapped
    :return: wrapper function
    """
    import time

    my_measure = -1
    measure: Mjerenje = Mjerenje()

    def wrapper(self, *args, **kwargs):
        nonlocal my_measure, measure  # grab vars outside the current scope
        if my_measure == -1:  # if no measure was done yet
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            my_measure = round((end - start) * 1000)  # measure the elapsed time
            this = self.num_of_processes - 1
            measure.measurements[this] = my_measure
            if my_measure != 0:  # calculate speedup and efficiency
                measure.speedup[this] = measure.measurements[0] / my_measure
                if self.num_of_processes != 0:
                    measure.efficiency[this] = measure.measurements[0] / (my_measure * self.num_of_processes)
                else:
                    measure.efficiency[this] = 0.0
            else:
                measure.speedup[this] = 0.0
                measure.efficiency = 0.0
            measure.write()  # write to file mjerenje.txt
        else:
            result = func(self, *args, **kwargs)
        return result

    return wrapper
