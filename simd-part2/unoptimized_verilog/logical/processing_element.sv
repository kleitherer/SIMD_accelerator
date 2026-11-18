`include "defines.sv"

module processing_element(

    // Clock and Reset Inputs
    input wire clk,
    input wire rst_n,

    // Input Instruction
    input pe_inst_t     pe_inst,
    input logic         pe_inst_valid,

    // Input Operands
    input logic [`PE_INPUT_BITWIDTH-1:0] vector_input,
    input logic [`PE_INPUT_BITWIDTH-1:0] matrix_input,

    // Output Operand
    output logic [`PE_OUTPUT_BITWIDTH-1:0] vector_output


);

    // START IMPLEMENTATION

    localparam int IN_W  = `PE_INPUT_BITWIDTH;
    localparam int OUT_W = `PE_OUTPUT_BITWIDTH;
    localparam int ACC_W = `PE_ACCUMULATION_BITWIDTH;
    localparam int MAX_LANES = 4;

    // Lane helpers (all lane math done in 64-bit signed)

    // Extract lane idx of width w from vec, sign-extended to 64 bits
    function automatic logic signed [63:0] get_lane(input logic [63:0] vec, input int idx, input int w);
        logic [63:0] tmp;
        tmp = vec >> (idx * w);
        tmp = tmp << (64 - w);
        return $signed(tmp) >>> (64 - w);
    endfunction

    // Overwrite lane idx of width w in vec with the low w bits of val
    function automatic logic [63:0] set_lane(input logic [63:0] vec, input int idx, input int w, input logic [63:0] val);
        logic [63:0] mask;
        mask = (w >= 64) ? {64{1'b1}} : ((64'd1 << w) - 64'd1);
        return (vec & ~(mask << (idx * w))) | ((val & mask) << (idx * w));
    endfunction

    // Clamp v into the signed range of a w-bit number
    function automatic logic signed [63:0] saturate(input logic signed [63:0] v, input int w);
        logic signed [63:0] max_v, min_v;
        max_v = (64'sd1 <<< (w - 1)) - 64'sd1;
        min_v = -(64'sd1 <<< (w - 1));
        if (v > max_v) return max_v;
        if (v < min_v) return min_v;
        return v;
    endfunction

    // v / 2**shift, round to nearest, ties to even (w = lane width)
    function automatic logic signed [63:0] round_ties_even(input logic signed [63:0] v, input int unsigned shift, input int w);
        logic [63:0] mask, half, low_bits;
        logic signed [63:0] rounded;
        if (shift == 0) return v;
        if (shift >= w) return 64'sd0;
        mask     = (64'd1 << shift) - 64'd1;
        half     = 64'd1 << (shift - 1);
        low_bits = v & mask;
        rounded  = v >>> shift;
        if (low_bits > half || (low_bits == half && rounded[0]))
            rounded = rounded + 64'sd1;
        return rounded;
    endfunction

    // State

    logic [ACC_W-1:0] acc_q, acc_d;
    logic [OUT_W-1:0] out_q, out_d;

    int  lane_w;     // input/output lane width: 8, 16, or 32
    int  num_lanes;  // 4, 2, or 1
    logic mode_ok;

    always_comb begin
        mode_ok = 1'b1;
        case (pe_inst.mode)
            `MODE_INT8:  lane_w = 8;
            `MODE_INT16: lane_w = 16;
            `MODE_INT32: lane_w = 32;
            default: begin lane_w = 32; mode_ok = 1'b0; end
        endcase
        num_lanes = IN_W / lane_w;
    end

    always_comb begin
        logic signed [63:0] a, b, acc;

        acc_d = acc_q;
        out_d = out_q;

        if (pe_inst_valid && mode_ok) begin
            if (pe_inst.opcode == `PE_RND_OPCODE) begin
                for (int i = 0; i < MAX_LANES; i++) begin
                    if (i < num_lanes) begin
                        acc   = get_lane(acc_q, i, 2 * lane_w);
                        acc_d = set_lane(acc_d, i, 2 * lane_w,
                                         round_ties_even(acc, pe_inst.value, 2 * lane_w));
                    end
                end
            end else if (pe_inst.opcode == `PE_MAC_OPCODE) begin
                case (pe_inst.value)
                    `PE_MAC_VALUE: begin
                        for (int i = 0; i < MAX_LANES; i++) begin
                            if (i < num_lanes) begin
                                a     = get_lane(vector_input, i, lane_w);
                                b     = get_lane(matrix_input, i, lane_w);
                                acc   = get_lane(acc_q, i, 2 * lane_w);
                                acc_d = set_lane(acc_d, i, 2 * lane_w, acc + a * b);
                            end
                        end
                    end
                    `PE_OUT_VALUE: begin
                        for (int i = 0; i < MAX_LANES; i++) begin
                            if (i < num_lanes) begin
                                acc   = get_lane(acc_q, i, 2 * lane_w);
                                out_d = set_lane(out_d, i, lane_w, saturate(acc, lane_w));
                            end
                        end
                    end
                    `PE_PASS_VALUE: begin
                        for (int i = 0; i < MAX_LANES; i++) begin
                            if (i < num_lanes) begin
                                a     = get_lane(vector_input, i, lane_w);
                                acc_d = set_lane(acc_d, i, 2 * lane_w, a);
                            end
                        end
                    end
                    `PE_CLR_VALUE: begin
                        acc_d = '0;
                        out_d = '0;
                    end
                    default: ; // NOP
                endcase
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_q <= '0;
            out_q <= '0;
        end else begin
            acc_q <= acc_d;
            out_q <= out_d;
        end
    end

    assign vector_output = out_q;

    // END IMPLEMENTATION

endmodule
