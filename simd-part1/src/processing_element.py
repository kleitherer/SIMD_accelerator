from bitstring import Bits
from .instruction import ProcessingElementInstruction, PEI
from dataclasses import dataclass

@dataclass
class ProcessingElementConfiguration:
    INPUT_BITWIDTH        : int
    ACCUMULATION_BITWIDTH : int
    OUTPUT_BITWIDTH       : int

class ProcessingElement:

    def __init__(
        self,
        config : ProcessingElementConfiguration,
        default_value = 0
    ):

        # Saving Inputs
        self._config = config

        # Creating Bitstrings
        self._input_a_value = Bits(int=default_value, length=self._config.INPUT_BITWIDTH)
        self._input_b_value = Bits(int=default_value, length=self._config.INPUT_BITWIDTH)
        self._acc_value     = Bits(int=default_value, length=self._config.ACCUMULATION_BITWIDTH)
        self._output_value  = Bits(int=default_value, length=self._config.OUTPUT_BITWIDTH)

    def input_a(self, value : Bits) -> None:
        self._input_a_value = value

    def input_b(self, value : Bits) -> None:
        self._input_b_value = value

    # Handling Each Instruction
    def execute_instruction(self, instruction : ProcessingElementInstruction) -> None:
        # START IMPLEMENTATION
        opcode = instruction.get_opcode().uint #have to make sure to convert to unsigned int
        value = instruction.get_value().uint

        if opcode == PEI.RND:
            self._handle_rnd(instruction)
        elif value == PEI.MAC:
            self._handle_mac(instruction)
        elif value == PEI.NOP:
            pass
        elif value == PEI.OUT:
            self._handle_out(instruction)
        elif value == PEI.PASS:
            self._handle_pass(instruction)
        elif value == PEI.CLR:
            self._handle_clr(instruction)
        # END IMPLEMENTATION
        return None

    
    #HANDLE FUNCS I WROTE FOR HANDLE MAC
    def split_lanes(x, lane_w, num_lanes):
        #lane 0 is least sig
        #split x into numlanes names w/ lanew widths per lane
         mask = (1 << lane_w) - 1   #drop last w bits
         lanes = []
         for i in range(num_lanes):from bitstring import Bits
from .instruction import ProcessingElementInstruction, PEI
from dataclasses import dataclass

@dataclass
class ProcessingElementConfiguration:
    INPUT_BITWIDTH        : int
    ACCUMULATION_BITWIDTH : int
    OUTPUT_BITWIDTH       : int

class ProcessingElement:

    def __init__(
        self,
        config : ProcessingElementConfiguration,
        default_value = 0
    ):

        # Saving Inputs
        self._config = config

        # Creating Bitstrings
        self._input_a_value = Bits(int=default_value, length=self._config.INPUT_BITWIDTH)
        self._input_b_value = Bits(int=default_value, length=self._config.INPUT_BITWIDTH)
        self._acc_value     = Bits(int=default_value, length=self._config.ACCUMULATION_BITWIDTH)
        self._output_value  = Bits(int=default_value, length=self._config.OUTPUT_BITWIDTH)

    def input_a(self, value : Bits) -> None:
        self._input_a_value = value

    def input_b(self, value : Bits) -> None:
        self._input_b_value = value

    # Handling Each Instruction
    def execute_instruction(self, instruction : ProcessingElementInstruction) -> None:
        # START IMPLEMENTATION
        # Your Code Here
        """
        The instruction input to the PE has three fields: Opcode, Mode, and Value.
        Mode tells us how many lanes
        Opcode tells us which instruction to implement
        # Field as the "Opcode"
        NO_VALUE = 0
        MAC      = 0
        NOP      = 1
        OUT      = 2
        PASS     = 3
        CLR      = 4

        # Instructions Which Require the Value Field
        RND      = 1
        """
        if instruction.get_opcode().uint == PEI.NO_VALUE:
            operation = instruction.get_value().uint
            if operation == PEI.MAC:
                self._handle_mac(instruction)
            elif operation == PEI.NOP:
                pass
            elif operation == PEI.OUT: # Saturate accumulator values to the output bit width and write the output register.
                self._handle_out(instruction)
            elif operation == PEI.PASS:
                self._handle_pass(instruction)
            elif operation == PEI.CLR:
                self._handle_clr(instruction)
        elif instruction.get_opcode().uint == PEI.RND:
            self._handle_rnd(instruction)

        # END IMPLEMENTATION
        return None

    def _handle_mac(self, instruction : ProcessingElementInstruction):
        # START IMPLEMENTATION
        # Your Code Here
        """
        The mode tells us how many lanes we need and how many pairings we need to call mac on
        """
        bit_width = instruction.get_mode_bitwidth()

        if bit_width == 8:
            # you need four 16-bit data lanes
            """
            There are four data inputs * four data inputs…
            so there are 4 simultaneous multiply and accumulate operations between the 4 pairs
            """
            a0 = self._input_a_value[0:8].int
            a1 = self._input_a_value[8:16].int
            a2 = self._input_a_value[16:24].int
            a3 = self._input_a_value[24:32].int
            b0 = self._input_b_value[0:8].int
            b1 = self._input_b_value[8:16].int
            b2 = self._input_b_value[16:24].int
            b3 = self._input_b_value[24:32].int
            acc0 = self._acc_value[0:16].int
            acc1 = self._acc_value[16:32].int
            acc2 = self._acc_value[32:48].int
            acc3 = self._acc_value[48:64].int
            # MAC does not saturate: mask to 16 bits so overflow wraps instead of erroring
            self._acc_value = Bits().join([
                Bits(uint=(acc0 + (a0 * b0)) & 0xFFFF, length=16),
                Bits(uint=(acc1 + (a1 * b1)) & 0xFFFF, length=16),
                Bits(uint=(acc2 + (a2 * b2)) & 0xFFFF, length=16),
                Bits(uint=(acc3 + (a3 * b3)) & 0xFFFF, length=16),
            ])
        elif bit_width == 16:
            a0 = self._input_a_value[0:16].int
            a1 = self._input_a_value[16:32].int
            b0 = self._input_b_value[0:16].int
            b1 = self._input_b_value[16:32].int
            acc0 = self._acc_value[0:32].int
            acc1 = self._acc_value[32:64].int
            # MAC does not saturate: mask to 32 bits so overflow wraps instead of erroring
            self._acc_value = Bits().join([
                Bits(uint=(acc0 + (a0 * b0)) & 0xFFFFFFFF, length=32),
                Bits(uint=(acc1 + (a1 * b1)) & 0xFFFFFFFF, length=32),
            ])
        elif bit_width == 32:
            """
            standard, there are no virtual lanes, it'll just get put into the main register
            there is just one mac that gets called
            """
            a0 = self._input_a_value[0:32].int
            b0 = self._input_b_value[0:32].int
            acc0 = self._acc_value[0:64].int
            # MAC does not saturate: mask to 64 bits so overflow wraps instead of erroring
            self._acc_value = Bits(uint=(acc0 + (a0 * b0)) & 0xFFFFFFFFFFFFFFFF, length=64)
        # END IMPLEMENTATION
        return None

    def _handle_out(self, instruction : ProcessingElementInstruction):
        # Clamp each signed wide lane to its signed output range; preserve accumulation.
        # START IMPLEMENTATION
        # Your Code Here
        bit_width = instruction.get_mode_bitwidth()

        if bit_width == 8: # Four 16-bit accumulator lanes, each clamped into an 8-bit output lane.
            acc0 = self._acc_value[0:16].int
            acc1 = self._acc_value[16:32].int
            acc2 = self._acc_value[32:48].int
            acc3 = self._acc_value[48:64].int
            out0 = min(max(acc0, -128), 127)
            out1 = min(max(acc1, -128), 127)
            out2 = min(max(acc2, -128), 127)
            out3 = min(max(acc3, -128), 127)
            self._output_value = Bits().join([
                Bits(int=out0, length=8),
                Bits(int=out1, length=8),
                Bits(int=out2, length=8),
                Bits(int=out3, length=8),
            ])
        elif bit_width == 16: # Two 32-bit accumulator lanes, each clamped into a 16-bit output lane.
            acc0 = self._acc_value[0:32].int
            acc1 = self._acc_value[32:64].int
            out0 = min(max(acc0, -32768), 32767)
            out1 = min(max(acc1, -32768), 32767)
            self._output_value = Bits().join([
                Bits(int=out0, length=16),
                Bits(int=out1, length=16),
            ])
        elif bit_width == 32: # One 64-bit accumulator lane, clamped into the 32-bit output register.
            acc0 = self._acc_value[0:64].int
            out0 = min(max(acc0, -2147483648), 2147483647)
            self._output_value = Bits(int=out0, length=32)
        # END IMPLEMENTATION
        return None

    def _handle_pass(self, instruction : ProcessingElementInstruction):
        # Sign-extend each input A lane into its accumulator lane. Leave the output unchanged.
        # START IMPLEMENTATION
        # Your Code Here
        bit_width = instruction.get_mode_bitwidth()

        if bit_width == 8:
            a0 = self._input_a_value[0:8].int
            a1 = self._input_a_value[8:16].int
            a2 = self._input_a_value[16:24].int
            a3 = self._input_a_value[24:32].int
            self._acc_value = Bits().join([
                Bits(int=a0, length=16),
                Bits(int=a1, length=16),
                Bits(int=a2, length=16),
                Bits(int=a3, length=16),
            ])
        elif bit_width == 16:
            a0 = self._input_a_value[0:16].int
            a1 = self._input_a_value[16:32].int
            self._acc_value = Bits().join([
                Bits(int=a0, length=32),
                Bits(int=a1, length=32),
            ])
        elif bit_width == 32:
            a0 = self._input_a_value[0:32].int
            self._acc_value = Bits(int=a0, length=64)
        # END IMPLEMENTATION
        return None

    def _handle_clr(self, instruction : ProcessingElementInstruction):
        # Zero every accumulator lane and every output lane.
        # START IMPLEMENTATION
        # Your Code Here
        bit_width = instruction.get_mode_bitwidth()

        if bit_width == 8:
            self._acc_value = Bits().join([
                Bits(int=0, length=16),
                Bits(int=0, length=16),
                Bits(int=0, length=16),
                Bits(int=0, length=16),
            ])
            self._output_value = Bits().join([
                Bits(int=0, length=8),
                Bits(int=0, length=8),
                Bits(int=0, length=8),
                Bits(int=0, length=8),
            ])
        elif bit_width == 16:
            self._acc_value = Bits().join([
                Bits(int=0, length=32),
                Bits(int=0, length=32),
            ])
            self._output_value = Bits().join([
                Bits(int=0, length=16),
                Bits(int=0, length=16),
            ])
        elif bit_width == 32:
            self._acc_value = Bits(int=0, length=64)
            self._output_value = Bits(int=0, length=32)
        # END IMPLEMENTATION
        return None

    def _handle_rnd(self, instruction : ProcessingElementInstruction):
        # Divide signed wide lanes by 2**unsigned(value), nearest with ties to even; preserve output.
        # START IMPLEMENTATION
        # Your Code Here
        bit_width = instruction.get_mode_bitwidth()
        shift = instruction.get_value().uint

        def round_ties_even(value):
            if shift == 0:
                return value
            half = 1 << (shift - 1)
            low_bits = value & ((1 << shift) - 1)
            rounded = value >> shift
            if low_bits > half or (low_bits == half and (rounded & 1)):
                rounded += 1
            return rounded

        if bit_width == 8:
            acc0 = round_ties_even(self._acc_value[0:16].int)
            acc1 = round_ties_even(self._acc_value[16:32].int)
            acc2 = round_ties_even(self._acc_value[32:48].int)
            acc3 = round_ties_even(self._acc_value[48:64].int)
            self._acc_value = Bits().join([
                Bits(int=acc0, length=16),
                Bits(int=acc1, length=16),
                Bits(int=acc2, length=16),
                Bits(int=acc3, length=16),
            ])
        elif bit_width == 16:
            acc0 = round_ties_even(self._acc_value[0:32].int)
            acc1 = round_ties_even(self._acc_value[32:64].int)
            self._acc_value = Bits().join([
                Bits(int=acc0, length=32),
                Bits(int=acc1, length=32),
            ])
        elif bit_width == 32:
            acc0 = round_ties_even(self._acc_value[0:64].int)
            self._acc_value = Bits(int=acc0, length=64)
        # END IMPLEMENTATION
        return None

    def get_output(self) -> Bits:
        return self._output_value

    def get_accumulation(self) -> Bits:
        return self._acc_value
