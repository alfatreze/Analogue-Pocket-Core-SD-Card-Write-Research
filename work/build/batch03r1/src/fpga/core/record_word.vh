// NCW1 format, wire words are big-endian (bridge_endian_little = 0).
// Independent byte oracle lives in tools/lab.py.
function automatic [31:0] record_word(input [3:0] index, input [31:0] generation);
    begin
        case (index)
            0: record_word = 32'h4e435731; // NCW1
            1: record_word = 32'd1;
            2: record_word = 32'd64;
            3: record_word = generation;
            4: record_word = 32'h00010001;
            default: record_word = (32'h10203040 + {index, 24'd0, index}) ^ generation;
        endcase
    end
endfunction
