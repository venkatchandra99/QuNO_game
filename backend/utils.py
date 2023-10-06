from qiskit import QuantumCircuit
from qiskit.visualization import circuit_drawer
from qiskit.visualization import plot_bloch_multivector, plot_state_qsphere

import matplotlib.pyplot as plt
import base64

import enum
import cmath
import random

# from gates import QuantumGates

class Constants(enum.Enum):
    R_angles = [0, cmath.pi, cmath.pi/2, -cmath.pi/2, cmath.pi/4, -cmath.pi/4, 3*cmath.pi/2, -3*cmath.pi/2]

class Operations():
    def __init__(self) -> None:
        pass
    
    def apply_quantum_gate(self, gate_name:str, qubit_indices:list, circuit:QuantumCircuit, *params):
        """ For a given name of quantum gate(string) applies that quantum gate to the qubits in the circuit provided.

        Args:
            gate_name (str): name of the gate
            qubit_indices (list): list of qubit/qubits the gate is being applied on
            circuit (QuantumCircuit): the quantum circuit in which gate should be applied to

        Raises:
            ValueError: Invalid number of qubits for gate. if given more that two gates
            ValueError: Unsupported gate name, if gate name is not supported
        """        
        
        gate_method = getattr(circuit, gate_name.lower(), None)

        if gate_method is not None:
            if len(qubit_indices) == 1:
                if params:
                    gate_method(*params, qubit_indices[0])
                else:
                    gate_method(qubit_indices[0])
            elif len(qubit_indices) == 2:
                if params:
                    gate_method(*params, qubit_indices[0], qubit_indices[1])
                else:
                    gate_method(qubit_indices[0], qubit_indices[1])
            else:
                raise ValueError("Invalid number of qubits for gate.")
        else:
            raise ValueError(f"Unsupported gate name: {gate_name}")
        
    def save_circuit_image(self, gates:list, qubits:list, angles:list, path:str = "game_state.png"):
        """Applies given gates on qubits provided and saves the image of quantum circuit in the specified path

        Args:
            gates (list): list of gates
            qubits (list): list of qubits the gate should be applied on 
            angles (list): List of angles for roatation gates, if angles are not required add None at that position
            path (str, optional): the path where the png file is to be saved. Defaults to "game_state.png".

        Raises:
            Exception: gates, qubits and angles lengths are not equal
        """        
        if len(gates) != len(qubits) !=len(angles):
            raise Exception("gates, qubits and angles lengths are not equal")
        max_qubits = max(item for sublist in qubits for item in sublist)+1
        qc = QuantumCircuit(max_qubits)
        for i in range(len(gates)):
            if angles[i] is not None:
                self.apply_quantum_gate(gates[i], qubits[i], qc, angles[i])
            else:
                self.apply_quantum_gate(gates[i], qubits[i], qc)
        image = circuit_drawer(qc, output='mpl')
        image.savefig(path, format='png')

    def save_bloch_sphere(state_vector:list, path:str = "bloch_sphere.png", reverse:bool= False):
        if reverse:
            state_vector = state_vector[::-1]
        bloch_fig = plot_bloch_multivector(state_vector)
        bloch_fig.savefig(path)
        plt.close(bloch_fig)
    
    def save_q_sphere(state_vector:list, path:str = "q_sphere.png", reverse:bool= False):
        if reverse:
            state_vector = state_vector[::-1]
        qsphere_fig = plot_state_qsphere(state_vector)    
        qsphere_fig.savefig(path)
        plt.close(qsphere_fig)

    def multiply_gates(self,  gate1, gate2):
        """ multiplies two given quantum gates

        Args:
            gate1 (matrix) 
            gate2 (matrix)

        Raises:
            ValueError: Matrix dimensions are incompatible for multiplication.

        Returns:
            matrix: Product matrix
        """        
        if len(gate1[0]) != len(gate2):
            raise ValueError("Matrix dimensions are incompatible for multiplication.")
        
        result = [[0 for _ in range(len(gate2[0]))] for _ in range(len(gate1))]

##        print("gate1:\n", gate1)
##        print("gate2:\n", gate2)

        for i in range(len(gate1)):
            for j in range(len(gate2[0])):
                for k in range(len(gate2)):
                    result[i][j] += (gate1[i][k]) * (gate2[k][j])
        return result

    def tensor_product(self, A, B):
        """Calculates the tensor product of the given two matrices or two lists, both must be either matrices or lists

        Args:
            A (matrix/ list): matrix or row Vector
            B (matrix/ list): matrix or row Vector

        Returns:
            matrix/ list: if both are matrices returns matrices, if both are row vectors returns row vecor.
        """        
        if isinstance(A[0], list) and isinstance(B[0], list):
            # If A and B are matrices
            m, n = len(A), len(A[0])
            p, q = len(B), len(B[0])

            result = [[0 for _ in range(n*q)] for _ in range(m*p)]

            for i in range(m):
                for j in range(n):
                    for k in range(p):
                        for l in range(q):
                            result[i*p + k][j*q + l] = A[i][j] * B[k][l]

        elif not isinstance(A[0], list) and not isinstance(B[0], list):
            # If A and B are vectors
            result = [a * b for a in A for b in B]
        return result

    def random_statevector(self, num_qubits):
        """ Creates a random statevector

        Args:
            num_qubits (int): number of qubits

        Returns:
            list: random statevector
        """        
        # Generate random complex numbers for the statevector
        statevector = [cmath.rect(1, 2*cmath.pi*random.random()) for _ in range(2**num_qubits)]
        
        # Normalize the statevector
        norm = sum(abs(coeff)**2 for coeff in statevector)**0.5
        statevector = [coeff / norm for coeff in statevector]
        
        return statevector

    def is_valid_statevector(self, statevector):
        """Checks if it is a valid statevector

        Args:
            statevector (list): row Vector
        Returns:
            bool
        """
        print("statevector valid", statevector)
        # Check if the length is a power of 2
        num_qubits = int(cmath.log(len(statevector), 2).real)
        if not 2**num_qubits == len(statevector):
            return False
        
        # Check if the statevector is normalized
        norm = sum(abs(coeff)**2 for coeff in statevector)
        return cmath.isclose(norm, 1)
    
    def fidelity(self, state1, state2):
        """ Calculates the fedility between two quantum states.

        Args:
            state1 (list): row Vector
            state2 (list): row Vector

        Raises:
            ValueError: States have different number of qubits

        Returns:
            complex number: fedility value
        """        
        # if len(state1) != len(state2):
        #     raise ValueError("States have different number of qubits.")
        
        inner_product = sum(a1 * a2.conjugate() for a1, a2 in zip(state1, state2))
        norm1 = cmath.sqrt(sum(abs(a)**2 for a in state1))
        norm2 = cmath.sqrt(sum(abs(a)**2 for a in state2))
        return abs(inner_product) / (norm1 * norm2)
    
    def row_to_coloumn_vector(self, row_vector:list):
        """ Converts a row vector to coloumn vector

        Args:
            row_vector (list): row vector (Eg: [1, 0])

        Returns:
            list: coloumn vector (Eg: [[1], [0]])
        """        
        col_vector = row_vector.copy()
        for i in range(len(col_vector)):
            col_vector[i] = [col_vector[i]]
        return col_vector

    def coloumn_to_row_vector(self, col_vector:list):
        """ Converts a coloumn vector to row vector

        Args:
            col_vector (list): coloumn vector (Eg: [[1], [0]])

        Returns:
            list: row_vector (Eg: [1, 0])
        """
        row_vector = col_vector.copy()
        for i in range(len(row_vector)):
            if len(row_vector[i])!=0:
                row_vector[i] = row_vector[i][0]
            else:
                row_vector[i] = 0
        return row_vector

    def num_qubits_required(self, unitary_matrix:list):
        """Calculates the number of qubits the unitary_matrix can be applied on.

        Args:
            unitary_matrix (matrix): list of list of complex numbers 

        Raises:
            ValueError: Input unitary_matrix is not a square matrix.
            ValueError: Input unitary_matrix is not unitary

        Returns:
            int: no. of qubits
        """

        # Get the number of rows and columns
        num_rows = len(unitary_matrix)
        num_cols = len(unitary_matrix[0])
        
        # Check if the matrix is square and unitary
        if num_rows != num_cols:
            raise ValueError("Input matrix is not a square matrix.")
        
        for i in range(num_rows):
            for j in range(num_cols):
                if abs(sum(unitary_matrix[i][k] * unitary_matrix[j][k].conjugate() for k in range(num_rows)) - (i == j)) > 1e-10:
                    raise ValueError("Input matrix is not unitary.")
        
        # Calculate the number of qubits required
        n = 0
        while 2**n != num_rows:
            n += 1
        
        return n

    def add_binary_inplace(self, binary_string:str, bit:int, position:int):
        """ Adds the bit in the binary_string in the given specfic position

        Args:
            binary_string (str): Original bit string
            bit (int): 0 or 1
            position (int): position it has to inserted (index starting from 0)

        Raises:
            ValueError: postion of bit to be inserted must be less than total number of bits
            ValueError: bit specified must be 0 or 1

        Returns:
            str: Total bit string with the inserted bit
        """   
        if position > len(binary_string):
            raise ValueError("postion of bit to be inserted must be less than total number of bits")
        if bit not in [0, 1]:
            raise ValueError("bit specified must be 0 or 1")
        
        output = binary_string.replace("0b", "")
        output = list(output)
        output.insert(position, bit)
        output = "".join(output)

        return output

    def int_to_binary(self, integer:int, L: int):
        """ Converts an integer to binary

        Args:
            integer (int)
            L (int): length of string, it will add zeros if front to the binary till length is matched

        Returns:
            str: binary string
        """
        binary = bin(integer).replace("0b", "")
        while len(binary) < L:
            binary = "0"+binary
        return binary
    
    def binary_to_int(self, binary:str):
        """ Converts binary to integer

        Args:
            binary (str): binary string

        Returns:
            int: number
        """        
        return int(binary, 2)

    def apply_two_qubit_gate(self, gate:list, qubits:list, total_qubits:int):
        """ gets unitary matrix for n qubits applying two qubit gate on given two qubits. (Verifiend only for CNOT gate and SWAP gate)

        Args:
            gate (list): matrix of the gate
            qubits (list): list of qubits you are applying the gate on.
            total_qubits (int): total no. of qubits present in the quantum circuit

        Returns:
            list: 2^total_qubits x 2^total_qubits matrix 
        """        
        total_gate = [[0 for _ in range(2**total_qubits)] for _ in range(2**total_qubits)]
        for i, row in enumerate(total_gate):
            ii = self.int_to_binary(i, total_qubits)
            _ii = "".join([ii[_] for _ in qubits])
            _ii = self.binary_to_int(_ii)
            rest_i = ""
            for a in range(len(ii)):
                if a not in qubits:
                    rest_i = rest_i+ii[a]
            for j, value in enumerate(row):
                jj = self.int_to_binary(j, total_qubits)
                _jj = "".join([jj[_] for _ in qubits])
                _jj = self.binary_to_int(_jj)
                # print(ii, jj, _ii, _jj, gate[_ii][_jj])
                rest_j = ""
                for a in range(len(jj)):
                    if a not in qubits:
                        rest_j = rest_j+jj[a]
                if rest_j == rest_i:
                    total_gate[i][j] = gate[_ii][_jj]

        return total_gate

    def get_total_unitary(self, unitary, total_qubits:int, qubit_num:list):
        """ Creates unirtary matrix of size 2**total_qubits x 2**total_qubits which applies the specified unitary on specified qubits.

        Args:
            unitary (list): Single qubit or double qubit gates
            total_qubits (int): total no. of qubits present in the circuit
            qubit_num (list): the qubit on which you want to apply gates on

        Raises:
            AttributeError: qubit_num cannot be an empty list

        Returns:
            list: Total unitary matrix.
        """        
        I = [[1, 0], [0, 1]]
        if len(qubit_num) == 0:
            raise AttributeError("Need to specify qubits to apply the gate")
        elif len(qubit_num) == 1:
            if qubit_num[0] == 0:
                end_state = unitary.copy()
            else:
                end_state = I.copy()
            for i in range(1, total_qubits):
                if i in qubit_num:
                    end_state = self.tensor_product(end_state, unitary)
                else:
                    Identity = I.copy()
                    end_state = self.tensor_product(end_state, Identity)
        elif len(qubit_num) == 2:
            end_state = self.apply_two_qubit_gate(gate=unitary, qubits=qubit_num, total_qubits= total_qubits)
        return end_state
    
    def normalize_statevector(self, statevector:list):
        """ Normalizes a given list

        Args:
            statevector (list): List that has to be normalized

        Raises:
            Exception: Internal Error

        Returns:
            list: normalized list.
        """        
        normalized_statevector = []
        comp_state = 0
        for state in statevector:
            if isinstance(state, int):
                comp_state = comp_state + state**2
            elif isinstance(state, complex):
                comp_state = comp_state + (state**2).real
        for state_index in range(len(statevector)):
            normalized_statevector.append(cmath.sqrt((statevector[state_index]**2)/comp_state))
        if not self.is_valid_statevector(statevector= normalized_statevector):
            raise Exception("Internal error: normalization of state gone wrong.")
        return normalized_statevector

    def reduce_statevector(self, statevector:list, qubit:int, measurment_value:int):
        """ removes the given qubit from the given state vector.

        Args:
            statevector (list)
            qubit (int): qubit you want to remove
            measurment_value (int): the measurment value

        Raises:
            Exception: Provided list is not a statevector

        Returns:
            list: Reduced statevector
        """        
        if not self.is_valid_statevector(statevector= statevector):
            raise Exception("Provided list is not a Statevector")
        if len(statevector) == 2:
            return []
        reduced_statevector = []
        for state_index in range(len(statevector)):
            binary = self.int_to_binary(state_index, int(cmath.log(len(statevector), 2).real))
            print(binary)
            if int(binary[qubit]) == measurment_value:
                reduced_statevector.append(statevector[state_index])
        print("reduced2:",reduced_statevector)
        normalized_statevector = self.normalize_statevector(reduced_statevector)
        return normalized_statevector

    def image_to_base64(self, file_path:str):
        with open(file_path, "rb") as image_file:
            image_data = image_file.read()
            base64_data = base64.b64encode(image_data).decode("utf-8")
            return base64_data




