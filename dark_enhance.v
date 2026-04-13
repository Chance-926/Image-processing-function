module dark_enhance_lut (
    input  wire        clk,         // 时钟信号
    input  wire        rst_n,       // 复位信号（低有效）

    input  wire [7:0]  pixel_in,    //输入像素值（0-255）
    input  wire        valid_in,    //输入信号是否有效

    output reg  [7:0]  pixel_out,   //输出像素值（经过 Gamma 0.5 增强）
    output reg         valid_out    //输出信号是否有效
);

    // ============================================================
    // LUT ROM（Gamma = 0.5 预计算）
    // ============================================================

    reg [7:0] lut [0:255];

    initial begin
        $readmemh("gamma_lut.mem", lut);
    end

    // ============================================================
    // 时序逻辑（对应 Python step）
    // ============================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pixel_out <= 8'd0;
            valid_out <= 1'b0;
        end
        else begin
            if (valid_in) begin
                pixel_out <= lut[pixel_in];  // 查表
                valid_out <= 1'b1;
            end
            else begin
                valid_out <= 1'b0;
            end
        end
    end

endmodule