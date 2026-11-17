from bitstring import Bits
from .instruction import MemoryInstruction, MI, Mode
from dataclasses import dataclass
import numpy as np

@dataclass
class MainBufferConfiguration:
    MEM0_BITWIDTH : int
    MEM0_DEPTH    : int
    MEM1_BITWIDTH : int
    MEM1_DEPTH    : int
    MEM2_BITWIDTH : int
    MEM2_DEPTH    : int

class MainBuffer:

    def __init__(
        self,
        config : MainBufferConfiguration,
        default_value = 0
    ):

        # Saving the Config
        self._buffer_config = config

        # Creating the Individual Memories
        self._mem0 = [Bits(int=default_value, length=self._buffer_config.MEM0_BITWIDTH) for _ in range(self._buffer_config.MEM0_DEPTH)]
        self._mem1 = [Bits(int=default_value, length=self._buffer_config.MEM1_BITWIDTH) for _ in range(self._buffer_config.MEM1_DEPTH)]
        self._mem2 = [Bits(int=default_value, length=self._buffer_config.MEM2_BITWIDTH) for _ in range(self._buffer_config.MEM2_DEPTH)]

        # Creating the Output And Input Ports
        self._mem0_output_port = Bits(int=default_value, length=self._buffer_config.MEM0_BITWIDTH)
        self._mem1_output_port = Bits(int=default_value, length=self._buffer_config.MEM1_BITWIDTH)
        self._mem2_input_port  = Bits(int=default_value, length=self._buffer_config.MEM2_BITWIDTH)

    def execute_instruction(self, instruction : MemoryInstruction) -> None:
        # START IMPLEMENTATION
        # Your Code Here
            #reads opcode and handles accordingly
        op = instruction.get_opcode().uint
        if op == MI.READ:
            self._handle_read(instruction)
        elif op == MI.WRITE:
            self._handle_write(instruction)
        # NOP = no action
        # END IMPLEMENTATION
        return None

    def _handle_read(self, instruction : MemoryInstruction) -> None:
        # START IMPLEMENTATION
        # Your Code Here
        a_off = instruction.get_mema_offset().uint
        b_off = instruction.get_memb_offset().uint
        w     = Mode.bitwidth(instruction.get_mode().uint)

        # MEM0: read the full 32 bit  word at MemAOffset + put at output port
        self._mem0_output_port = self._mem0[a_off]

        # MEM1: upper bits say which 32 bit word to read
            # lower bits say which piece of that word to pick
            # piece copied to fill all 32 bits
        word_w   = self._buffer_config.MEM1_BITWIDTH
        pieces   = word_w // w                        # how many pieces fit into one word
        sel_bits = pieces.bit_length() - 1            # how many address bits needed to specify which number
        addr     = b_off >> sel_bits                  # MemBOffset[MSB:sel_bits] but shift + mask (drop bottom bits)
        sel      = b_off & (pieces - 1)               # MemBOffset[sel_bits-1:0] (keep only bottom bits)

        word  = self._mem1[addr].uint #go read the number u want from word
        piece = (word >> (sel * w)) & ((1 << w) - 1)  # sel0= least sig
        rep = 0
        for i in range(pieces): 
            rep |= piece << (i * w) #paste number into every slot to fill whole world
        self._mem1_output_port = Bits(uint=rep, length=word_w) #put new word on output so PEs can use it
        # END IMPLEMENTATION
        return None

    def _handle_write(self, instruction : MemoryInstruction) -> None:
        # START IMPLEMENTATION
        # Your Code Here
        a_off = instruction.get_mema_offset().uint
        self._mem2[a_off] = self._mem2_input_port
        # END IMPLEMENTATION
        return None

    def read_mem0_output(self) -> Bits:
        return self._mem0_output_port

    def read_mem1_output(self) -> Bits:
        return self._mem1_output_port

    def write_mem2_input(self, value : Bits) -> None:
        self._mem2_input_port = value

    def set_mem0(self, mem : list[int]) -> None:
        # Ensuring the Memory List is the Proper Length and Writing
        if len(mem) != self._buffer_config.MEM0_DEPTH:
            raise ValueError(f"Length of Memory [{len(mem)}] is incorrect for depth [{self._buffer_config.MEM0_DEPTH}] ")
        self._mem0 = [Bits(int=elem, length=self._buffer_config.MEM0_BITWIDTH) for elem in mem]

    def set_mem1(self, mem : list[int]) -> None:
        # Ensuring the Memory List is the Proper Length and Writing
        if len(mem) != self._buffer_config.MEM1_DEPTH:
            raise ValueError(f"Length of Memory [{len(mem)}] is incorrect for depth [{self._buffer_config.MEM1_DEPTH}] ")
        self._mem1 = [Bits(int=elem, length=self._buffer_config.MEM1_BITWIDTH) for elem in mem]

    def set_mem0_bits(self, mem : list[Bits]) -> None:
        # Ensuring the Memory List is the Proper Length and Writing
        if len(mem) != self._buffer_config.MEM0_DEPTH:
            raise ValueError(f"Length of Memory [{len(mem)}] is incorrect for depth [{self._buffer_config.MEM0_DEPTH}] ")
        self._mem0 = mem

    def set_mem1_bits(self, mem : list[Bits]) -> None:
        # Ensuring the Memory List is the Proper Length and Writing
        if len(mem) != self._buffer_config.MEM1_DEPTH:
            raise ValueError(f"Length of Memory [{len(mem)}] is incorrect for depth [{self._buffer_config.MEM1_DEPTH}] ")
        self._mem1 = mem

    def read_mem2(self) -> list[int]:
        return [elem.int for elem in self._mem2]

    def read_mem2_bits(self) -> list[Bits]:
        return self._mem2
