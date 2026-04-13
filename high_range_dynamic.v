module hdr_lut (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  pixel_in,
    input  wire        valid_in,

    output reg  [7:0]  pixel_out,
    output reg         valid_out
);

    // ============================================================
    // LUT ROM（256×8bit）
    // ============================================================
    reg [7:0] lut [0:255];

    // 推荐：用mem文件加载（最规范）
    initial begin
        $readmemh("hdr_lut.mem", lut);
    end

    // ============================================================
    // 时序逻辑（1拍输出）
    // ============================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pixel_out <= 8'd0;
            valid_out <= 1'b0;
        end
        else begin
            if (valid_in) begin
                pixel_out <= lut[pixel_in];
                valid_out <= 1'b1;
            end
            else begin
                valid_out <= 1'b0;
            end
        end
    end

endmodule