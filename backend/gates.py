from enum import Enum
import random
import cmath

from utils import Operations

class QuantumGates(Enum):
    I = [[1, 0], [0, 1]]
    X = [[0, 1], [1, 0]]
    Y = [[0, -1j], [1j, 0]]
    Z = [[1, 0], [0, -1]]
    H = [[(1+0j)/cmath.sqrt(2), (1+0j)/cmath.sqrt(2)], [(1+0j)/cmath.sqrt(2), -(1+0j)/cmath.sqrt(2)]]
    S = [[1, 0], [0, 1j]]
    T = [[1, 0], [0, cmath.exp(1j*cmath.pi/4)]]
    TDAGGER = [[1, 0], [0, cmath.exp(-1j*cmath.pi/4)]]
    SDAGGER = [[1, 0], [0, -1j]]

    Rx = lambda theta: [[cmath.cos(theta/2), -1j*cmath.sin(theta/2)], [-1j*cmath.sin(theta/2), cmath.cos(theta/2)]]
    Ry = lambda theta: [[cmath.cos(theta/2), -cmath.sin(theta/2)], [cmath.sin(theta/2), cmath.cos(theta/2)]]
    Rz = lambda theta: [[cmath.exp(-1j*theta/2), 0], [0, cmath.exp(1j*theta/2)]]

    CNOT = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]
    SWAP = [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]

    def add_qubit(statevector:list)-> list:
        new_statevector = statevector.copy()
        states = len(statevector)
        for i in range(states):
            new_statevector.append(0)
        return new_statevector

    def measure_and_remove_qubit(qubit:int, statevector:list)-> (int, list):
        states = len(statevector)
        binary_0 = 0
        binary_1 = 0
        for i in range(states):
            amplitude = statevector[i] 
            binary = Operations().int_to_binary(i, int(cmath.log(states, 2).real))
            if binary[qubit] == '0' and (isinstance(amplitude, int) or isinstance(amplitude, float)):
                binary_0 = binary_0 + abs(amplitude**2)
            elif binary[qubit] == '0' and isinstance(amplitude, complex):
                binary_0 = binary_0 + abs((amplitude**2).real)
            elif binary[qubit] == '1' and (isinstance(amplitude, int) or isinstance(amplitude, float)):
                binary_1 = binary_1 + abs(amplitude**2)
            elif binary[qubit] == '1' and isinstance(amplitude, complex):
                binary_1 = binary_1 + abs((amplitude**2).real)
            print("measures:", binary_0, binary_1)
        measurement = random.choices([0, 1], [binary_0, binary_1])[0]
        reduced_statevector = Operations().reduce_statevector(statevector= statevector, qubit= qubit, measurment_value= measurement)
        print("reduced:",reduced_statevector)
        return measurement, reduced_statevector
    
