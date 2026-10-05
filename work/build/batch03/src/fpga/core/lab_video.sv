`default_nettype none
// Small readable 320x240 diagnostic display, template video timing at 12.288 MHz.
module lab_video #(parameter integer BUILD_NUMBER=2)(input wire clk, input wire reset_n,
    input wire [3:0] status, input wire [31:0] generation, loaded_generation, completed,
    input wire [2:0] error, input wire [31:0] elapsed,
    output reg [23:0] rgb = 0, output reg de = 0, hs = 0, vs = 0);
reg [9:0] x = 0, y = 0;
function automatic [7:0] hex_digit(input [3:0] n);
    hex_digit = n < 10 ? 8'd48 + n : 8'd65 + n - 10;
endfunction
function automatic [63:0] hex_word(input [31:0] value);
    integer digit;
    begin
        for (digit=0; digit<8; digit=digit+1)
            hex_word[63-digit*8 -: 8] = hex_digit(value[31-digit*4 -: 4]);
    end
endfunction
function automatic [34:0] glyph(input [7:0] c);
    begin
        case(c)
            8'd32: glyph = 35'h000000000;
            8'd65: glyph = 35'h3a31fc631;
            8'd66: glyph = 35'h7a31f463e;
            8'd67: glyph = 35'h3e108420f;
            8'd68: glyph = 35'h7a318c63e;
            8'd69: glyph = 35'h7e10f421f;
            8'd70: glyph = 35'h7e10f4210;
            8'd71: glyph = 35'h3e10bc62f;
            8'd72: glyph = 35'h4631fc631;
            8'd73: glyph = 35'h7c842109f;
            8'd74: glyph = 35'h1c4214a4c;
            8'd75: glyph = 35'h4654c5251;
            8'd76: glyph = 35'h42108421f;
            8'd77: glyph = 35'h4775ac631;
            8'd78: glyph = 35'h47359c631;
            8'd79: glyph = 35'h3a318c62e;
            8'd80: glyph = 35'h7a31f4210;
            8'd81: glyph = 35'h3a318d64d;
            8'd82: glyph = 35'h7a31f5251;
            8'd83: glyph = 35'h3e107043e;
            8'd84: glyph = 35'h7c8421084;
            8'd85: glyph = 35'h46318c62e;
            8'd86: glyph = 35'h46318c544;
            8'd87: glyph = 35'h4631ad771;
            8'd88: glyph = 35'h462a22a31;
            8'd89: glyph = 35'h462a21084;
            8'd90: glyph = 35'h7c222221f;
            8'd48: glyph = 35'h3a33ae62e;
            8'd49: glyph = 35'h11842108e;
            8'd50: glyph = 35'h3a211111f;
            8'd51: glyph = 35'h78217043e;
            8'd52: glyph = 35'h08ca97c42;
            8'd53: glyph = 35'h7e10f043e;
            8'd54: glyph = 35'h3a10f462e;
            8'd55: glyph = 35'h7c2222108;
            8'd56: glyph = 35'h3a317462e;
            8'd57: glyph = 35'h3a317842e;
            default: glyph = 0;
        endcase
    end
endfunction
reg [191:0] line_text;
reg [7:0] character;
reg [34:0] bitmap;
integer vx, vy, line_no, column, gx, gy;
reg ink;
always @(*) begin
    vx = x - 10;
    vy = y - 10;
    line_no = (vy-12)/20;
    column = (vx-16)/12;
    gx = ((vx-16)%12)/2;
    gy = ((vy-12)%20)/2;
    line_text = "                        ";
    case(line_no)
        0: line_text = "CARD WRITING LAB 02     ";
        1: line_text = "A WRITE  B READ         ";
        2: line_text = "CMD STATUS              ";
        4: line_text = "EXPECT GEN 00000000     ";
        5: line_text = "READ GEN   00000000     ";
        6: line_text = "COMPLETE   00000000     ";
        7: line_text = "ERROR      0            ";
        8: line_text = "CYCLES     00000000     ";
        9: line_text = "CHECK FILE ON COMPUTER  ";
        10: line_text = "AFTER QUIT AND RESTART  ";
        3: case(status)
            0: line_text = "IDLE                    ";
            1: line_text = "PREPARING               ";
            2: line_text = "WAITING                 ";
            3: line_text = "WRITE CMD OK            ";
            4: line_text = "READ MATCH              ";
            5: line_text = "READ DIFF               ";
            6: line_text = "COMMAND ERROR           ";
            7: line_text = "TIMEOUT RESTART         ";
            default: line_text = "UNKNOWN                 ";
        endcase
    endcase
    if (BUILD_NUMBER == 3) begin
        case(line_no)
            0: line_text = "SD WRITE RESEARCH B003  ";
            1: line_text = "A RUN  B COLD READ      ";
            2: line_text = "BATCH STATUS            ";
            3: case(status)
                0: line_text = "READY 32 CASES          ";
                1: line_text = "PREPARING               ";
                2: line_text = "RUNNING                 ";
                4: line_text = "BATCH PASS              ";
                5: line_text = "BATCH FAIL              ";
                7: line_text = "TIMEOUT STOPPED         ";
                default: line_text = "BATCH ERROR             ";
            endcase
            4: line_text = "CASE       00000000     ";
            5: line_text = "PASSED     00000000     ";
            6: line_text = "FINISHED   00000000     ";
            9: line_text = "SCREEN IS READBACK ONLY ";
            10: line_text = "CHECK FILE ON COMPUTER  ";
        endcase
    end
    if (line_no == 4) line_text[103 -: 64] = hex_word(generation);
    if (line_no == 5) line_text[103 -: 64] = hex_word(loaded_generation);
    if (line_no == 6) line_text[103 -: 64] = hex_word(completed);
    if (line_no == 7) line_text[103 -: 8] = hex_digit({1'b0,error});
    if (line_no == 8) line_text[103 -: 64] = hex_word(elapsed);
    character = 32;
    if (column >= 0 && column < 24) character = line_text[191-column*8 -: 8];
    bitmap = glyph(character);
    ink = 0;
    if (vx >= 16 && vx < 304 && vy >= 12 && vy < 232 &&
        gx >= 0 && gx < 5 && gy >= 0 && gy < 7)
        ink = bitmap[34-gy*5-gx];
end
always @(posedge clk) begin
    if (!reset_n) begin x <= 0; y <= 0; rgb <= 0; de <= 0; hs <= 0; vs <= 0; end
    else begin
        x <= x + 1'b1;
        if (x == 399) begin x <= 0; y <= y == 511 ? 0 : y+1'b1; end
        hs <= x == 3;
        vs <= x == 0 && y == 0;
        de <= x >= 10 && x < 330 && y >= 10 && y < 250;
        rgb <= 0;
        if (x >= 10 && x < 330 && y >= 10 && y < 250) begin
            rgb <= 24'h101820;
            if (ink) begin
                rgb <= 24'hdce9e9;
                if (line_no == 3) rgb <= status >= 5 ? 24'hff8866 : 24'h7ce8c4;
            end
        end
    end
end
endmodule
`default_nettype wire
