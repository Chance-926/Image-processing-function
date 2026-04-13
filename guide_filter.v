module guided_filter_3x3 #(
    parameter IMG_WIDTH = 640,
    parameter THRESHOLD = 8'd20
)(
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  pixel_in,
    input  wire        valid_in,

    output reg  [7:0]  pixel_out,
    output reg         valid_out
);

    // ============================================================
    // 行缓存（2行）
    // ============================================================
    reg [7:0] line_buf0 [0:IMG_WIDTH-1];
    reg [7:0] line_buf1 [0:IMG_WIDTH-1];

    reg [15:0] x_cnt;

    // ============================================================
    // 3×3窗口寄存器
    // ============================================================
    reg [7:0] w00, w01, w02;
    reg [7:0] w10, w11, w12;
    reg [7:0] w20, w21, w22;

    // ============================================================
    // 主逻辑
    // ============================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_cnt     <= 0;
            valid_out <= 0;
        end
        else if (valid_in) begin

            // =============================
            // 更新窗口（Shift）
            // =============================
            w00 <= w01;
            w01 <= w02;
            w02 <= line_buf1[x_cnt];

            w10 <= w11;
            w11 <= w12;
            w12 <= line_buf0[x_cnt];

            w20 <= w21;
            w21 <= w22;
            w22 <= pixel_in;

            // =============================
            // 更新行缓存
            // =============================
            line_buf1[x_cnt] <= line_buf0[x_cnt];
            line_buf0[x_cnt] <= pixel_in;

            // =============================
            // 计算 mean（9点平均）
            // =============================
            wire [11:0] sum =
                w00 + w01 + w02 +
                w10 + w11 + w12 +
                w20 + w21 + w22;

            wire [7:0] mean = sum >>3;  // 可优化为 >>3

            // =============================
            // 计算 max/min（展开比较）
            // =============================
            wire [7:0] max0 = (w00 > w01) ? w00 : w01;
            wire [7:0] max1 = (w02 > w10) ? w02 : w10;
            wire [7:0] max2 = (w11 > w12) ? w11 : w12;
            wire [7:0] max3 = (w20 > w21) ? w20 : w21;
            wire [7:0] max4 = (w22 > max0) ? w22 : max0;
            wire [7:0] max5 = (max1 > max2) ? max1 : max2;
            wire [7:0] max6 = (max3 > max4) ? max3 : max4;
            wire [7:0] max_v = (max5 > max6) ? max5 : max6;

            wire [7:0] min0 = (w00 < w01) ? w00 : w01;
            wire [7:0] min1 = (w02 < w10) ? w02 : w10;
            wire [7:0] min2 = (w11 < w12) ? w11 : w12;
            wire [7:0] min3 = (w20 < w21) ? w20 : w21;
            wire [7:0] min4 = (w22 < min0) ? w22 : min0;
            wire [7:0] min5 = (min1 < min2) ? min1 : min2;
            wire [7:0] min6 = (min3 < min4) ? min3 : min4;
            wire [7:0] min_v = (min5 < min6) ? min5 : min6;

            wire [7:0] var = max_v - min_v;

            // =============================
            // 自适应滤波（核心）
            // =============================
            if (var < THRESHOLD)
                pixel_out <= mean;
            else
                pixel_out <= w11;  // 中心像素

            valid_out <= 1'b1;

            // =============================
            // x计数
            // =============================
            if (x_cnt == IMG_WIDTH - 1)
                x_cnt <= 0;
            else
                x_cnt <= x_cnt + 1;

        end
        else begin
            valid_out <= 1'b0;
        end
    end

endmodule