from dataclasses import dataclass
from bitstring import Bits
from .processing_element import ProcessingElement, ProcessingElementConfiguration
from .main_buffer import MainBuffer, MainBufferConfiguration
from .instruction import Instruction, MemoryInstruction, ProcessingElementInstruction
import copy


@dataclass
class AcceleratorConfiguration:

    # Top Level Specific Values
    COUNTER_BITWIDTH : int
    PE_COUNT         : int

    # Internal Buffer/PE Configurations
    PE_CONFIG        : ProcessingElementConfiguration
    BUFFER_CONFIG    : MainBufferConfiguration

    # Function to Validate Configuration
    def validate(self) -> None:

        # Ensuring the Width of the Main Buffer Matches the
        # Number of PEs in the Array accounting for Input Width
        if (self.PE_COUNT != (self.BUFFER_CONFIG.MEM0_BITWIDTH/self.PE_CONFIG.INPUT_BITWIDTH)):
            raise ValueError(f"Incorrect number of PEs ({self.PE_COUNT}) with input bitwidth {self.PE_CONFIG.INPUT_BITWIDTH} for memory output bitwidth {self.BUFFER_CONFIG.MEM0_BITWIDTH}.")

        # Ensuring the Width of the Main Buffer Matches the PE input bitwidth
        if (self.PE_CONFIG.INPUT_BITWIDTH != self.BUFFER_CONFIG.MEM1_BITWIDTH):
            raise ValueError(f"Incorrect PE input bitwidth {self.PE_CONFIG.INPUT_BITWIDTH} for memory bitwidth {self.BUFFER_CONFIG.MEM1_BITWIDTH}.")

        # Ensuring the Width of the Main Buffer Matches the PE output bitwidth
        if (self.PE_COUNT != (self.BUFFER_CONFIG.MEM2_BITWIDTH/self.PE_CONFIG.OUTPUT_BITWIDTH)):
            raise ValueError(f"Incorrect number of PEs ({self.PE_COUNT}) with output bitwidth {self.PE_CONFIG.OUTPUT_BITWIDTH} for memory input bitwidth {self.BUFFER_CONFIG.MEM2_BITWIDTH}.")
AccelConfig=AcceleratorConfiguration


class Accelerator:

    def __init__(
        self,
        controller_config : AcceleratorConfiguration,
        default_counter_value = 0
    ):

        # Saving the Configuration and Validating
        self._controller_config = controller_config
        self._controller_config.validate()

        # Creating a Bit-Accurate Representation of the Counter
        self._counter = Bits(uint=default_counter_value, length=self._controller_config.COUNTER_BITWIDTH)

        # Creating an Array of PEs
        self._pe_array = [
            ProcessingElement(self._controller_config.PE_CONFIG) for _ in range(self._controller_config.PE_COUNT)
        ]

        # Creating a Main Buffer
        self._main_buffer = MainBuffer(self._controller_config.BUFFER_CONFIG)

    def set_memory(self, mem0 : list[Bits], mem1 : list[Bits]) -> None:
        self.set_mem0(mem0)
        self.set_mem1(mem1)

    def set_mem0(self, mem : list[Bits]) -> None:
        self._main_buffer.set_mem0_bits(mem)

    def set_mem1(self, mem : list[Bits]) -> None:
        self._main_buffer.set_mem1_bits(mem)

    def get_mem2(self) -> list[Bits]:
        return self._main_buffer.read_mem2_bits()

    def execute_instructions(self, instructions : list[Instruction]):
        for inst in instructions:
            self.execute_instruction(inst)

    def execute_instruction(self, instruction : Instruction):
        # START IMPLEMENTATION
        # Your Code Here

        # split instruction into its parts (unpack)
        mem_inst = instruction.get_mem_instruction()
        pe_inst  = instruction.get_pe_instruction()
        count    = instruction.get_count().uint
        mema_inc = instruction.get_mema_inc().uint
        memb_inc = instruction.get_memb_inc().uint

        # starting positions, use mask as before for desired wrap behavior
        a_off  = mem_inst.get_mema_offset().uint
        b_off  = mem_inst.get_memb_offset().uint
        a_mask = (1<<len(mem_inst.get_mema_offset()))- 1
        b_mask = (1<<len(mem_inst.get_memb_offset()))-1

        #get widths read from config
        n_pe  = self._controller_config.PE_COUNT
        in_w  = self._controller_config.PE_CONFIG.INPUT_BITWIDTH
        out_w = self._controller_config.PE_CONFIG.OUTPUT_BITWIDTH
        cnt_mask = (1 <<self._controller_config.COUNTER_BITWIDTH)-1

        # do/repeat step count +1 times (bc count means how many extra times to repeat)
        for i in range(count + 1):
            self._counter = Bits(uint=i & cnt_mask, length=self._controller_config.COUNTER_BITWIDTH)

            #prepare current (this round) memory instruct
            cur_mem = copy.deepcopy(mem_inst)
            cur_mem.set_mema_offset(a_off)
            cur_mem.set_memb_offset(b_off)

            # concat every pe  output reg into one wide word for MEM2 (collect components of output vector)
            #count 0 from least sig end
            out_word = 0
            for p,pe in enumerate(self._pe_array):
                #get pe's 32 bit answer (p) as number and merge into outword (put pe answers side by side)
                out_word |= pe.get_output().uint << (p * out_w)
                #put all PE outputs on MEM2 input port so buffer stores them only if WRITE
            self._main_buffer.write_mem2_input(Bits(uint=out_word, length=n_pe * out_w))

            # run mem instruction (read, write, nop)
            self._main_buffer.execute_instruction(cur_mem)

            # get data the buffer just read
            mem0_word = self._main_buffer.read_mem0_output().uint #grab word just read by MEM0 (will be wide bc consists of every pe's data tgt)
            mem1_word = self._main_buffer.read_mem1_output() #grab word mem1 read
            in_mask   = (1 << in_w) - 1
            for p, pe in enumerate(self._pe_array):
                pe.input_a(mem1_word)   # broadcast same vector val to every PE
                pe.input_b(Bits(uint=(mem0_word >> (p * in_w)) & in_mask, length=in_w)) #cut into section nad hand to separate PEs
                pe.execute_instruction(pe_inst)   # same instruction to every PE bs simd

            # increment the offsets for the next repeat incl masks
            a_off = (a_off + mema_inc) & a_mask
            b_off = (b_off + memb_inc) & b_mask

        # END IMPLEMENTATION
        return 0
