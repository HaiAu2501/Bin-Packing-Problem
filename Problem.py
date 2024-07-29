from typing import List, Tuple, Callable, Optional
import numpy as np

class Problem:
    def __init__(self, path: str):
        self.path = path
        self.load_data()
        self.total_items = self.n_items * self.n_bins
        self.used_bins = self.total_items
        self.loads = None
        self.best_fitness = np.inf

    def load_data(self):
        with open(self.path, 'r') as file:
            lines = file.readlines()
        
        self.bin_size = tuple(map(int, lines[0].split()[2:]))
        self.n_bins = int(lines[1].strip().split()[3])
        self.n_items = int(lines[2].strip().split()[5])
        self.total_volume = int(lines[3].strip().split()[4])
        self.items = []

        for line in lines[5:]:
            item = tuple(map(int, line.strip().split()))
            self.items.append(item)

        print(f'Loaded data from {self.path}')
        print(f'Problem: {self.n_items} items | {self.n_bins} bins | {self.bin_size} | {self.total_volume}')
    
class Placement:
    class Bin:
        def __init__(self, size: Tuple[int]):
            self.size = size
            self.EMSs: List[List[Tuple[int]]] = [
                [(0, 0, 0), size] # Each EMS is a list of 2 tuples, the first one is always like this
            ]
            self.load = 0

        # Return the EMS is chosen to place the item based on Distance to Front-Top-Right Corner (FTR) rule
        def choose(self, item: Tuple[int]) -> Tuple[int]:
            max_distance = -1
            selected_EMS = None
            for EMS in self.EMSs:
                if self.fit(item, EMS):
                    x, y, z = EMS[0][0] + item[0], EMS[0][1] + item[1], EMS[0][2] + item[2]
                    distance = (self.size[0] - x) ** 2 + (self.size[1] - y) ** 2 + (self.size[2] - z) ** 2
                    if distance > max_distance:
                        max_distance = distance
                        selected_EMS = EMS
            return selected_EMS
        
        @staticmethod
        def fit(item: Tuple[int], EMS: List[Tuple[int]]) -> bool:
            for i in range(3):
                if EMS[0][i] + item[i] > EMS[1][i]: return False
            return True

        """
        @staticmethod
        def overlapped(EMS1: List[Tuple[int]], EMS2: List[Tuple[int]]) -> bool:
            return np.all(EMS1[0] < EMS2[1]) and np.all(EMS1[1] > EMS2[0]) # EMS1 is overlapped with EMS2
        """
        @staticmethod
        def inscribed(EMS1: List[Tuple[int]], EMS2: List[Tuple[int]]) -> bool:
            return np.all(EMS1[0] >= EMS2[0]) and np.all(EMS1[1] <= EMS2[1]) # EMS1 is inscribed in EMS2

        # Update EMSs after placing the item into the chosen EMS
        def update(self, item: Tuple[int], selected_EMS: Tuple[int]) -> None:
            x1, y1, z1 = selected_EMS[0]
            x2, y2, z2 = x1 + item[0], y1 + item[1], z1 + item[2]
            x3, y3, z3 = selected_EMS[1]

            new_EMSs = [
                [(x2, y1, z1), (x3, y3, z3)],
                [(x1, y2, z1), (x3, y3, z3)],
                [(x1, y1, z2), (x3, y3, z3)]
            ]

            self.EMSs.remove(selected_EMS)
            for EMS in new_EMSs:
                isValid = True
                for i in range(3):
                    if EMS[0][i] >= EMS[1][i]:
                        isValid = False
                        break

                for other_EMS in self.EMSs:
                    if self.inscribed(EMS, other_EMS):
                        isValid = False
                        break

                if isValid:
                    self.EMSs.append(EMS)

            self.load += item[0] * item[1] * item[2]

    def __init__(self, problem: Problem):
        self.problem = problem
        self.bin_size = problem.bin_size
        self.n_bins = problem.n_bins
        self.n_items = problem.n_items
        self.total_volume = problem.total_volume
        self.items = problem.items

        self.used_bins = 1
        self.total_items = self.n_items * self.n_bins
        self.bins = [self.Bin(self.bin_size)]
        self.loads = None

    @staticmethod
    def get_orientation(gene: float) -> int:
        return int(np.ceil(6 * gene))
    
    @staticmethod
    def get_size(item: Tuple[int], orientation: int) -> Tuple[int]:
        x, y, z = item
        if   orientation == 1: return (x, y, z)
        elif orientation == 2: return (x, z, y)
        elif orientation == 3: return (y, x, z)
        elif orientation == 4: return (y, z, x)
        elif orientation == 5: return (z, x, y)
        elif orientation == 6: return (z, y, x)

    def decode(self, solution) -> None:
        if len(solution) != 2 * self.total_items:
            raise ValueError('Invalid solution length')
        
        orders = np.argsort(solution[:self.total_items])

        for i in range(self.total_items):
            item = self.items[i]
            orientation = self.get_orientation(solution[self.total_items + i])
            size = self.get_size(item, orientation)
            self.items[orders[i]] = size

    def evaluate(self, solution: List[float]) -> float:
        self.decode(solution)
        
        for item in self.items:
            selected_bin = None
            selected_EMS = None

            for bin in self.bins:
                EMS = bin.choose(item)
                if EMS is not None:
                    selected_bin = bin
                    selected_EMS = EMS

                if selected_bin is None:
                    self.used_bins += 1
                    self.bins.append(self.Bin(self.bin_size))
                    selected_bin = self.bins[-1]
                    selected_EMS = selected_bin.EMSs[0]

            selected_bin.update(item, selected_EMS)

        self.loads = [bin.load for bin in self.bins]
        least_load = np.min(self.loads) / (self.bin_size[0] * self.bin_size[1] * self.bin_size[2])
        fitness = self.used_bins + least_load

        if fitness < self.problem.best_fitness:
            self.problem.used_bins = self.used_bins
            self.problem.best_fitness = fitness
            self.problem.loads = self.loads

        return fitness # To maximize the fitness
    
if 11 < 3:
    problem = Problem('Data/Dataset/test.dat')
    placement = Placement(problem)
    solution = np.random.rand(2 * problem.total_items)
    fitness = placement.evaluate(solution)
    print(f'Fitness: {fitness} | Used bins: {placement.used_bins} | Loads: {placement.problem.loads}')

if 11 < 3:
    list = [1, 2, 3]
    for i in list:
        print(i)
        if i == 2:
            list.remove(3)