module upscale_x2 (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  pixel_in,
    input  wire        valid_in,

    output reg  [7:0]  pixel_out,
    output reg         valid_out
);

    // ============================================================
    // 行缓存（保存上一行）
    // ============================================================
    reg [7:0] line_buf [0:1023];  // 假设最大宽度1024
    reg [10:0] x_cnt;

    reg [7:0] p00, p01, p10, p11;

    // 当前行前一个像素
    reg [7:0] prev_pixel;

    // 奇偶控制（对应 dx, dy）
    reg x_phase;  // 0/1
    reg y_phase;  // 0/1

    // ============================================================
    // 主逻辑
    // ============================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_cnt     <= 0;
            x_phase   <= 0;
            y_phase   <= 0;
            valid_out <= 0;
        end
        else if (valid_in) begin

            // 读取邻域
            p00 <= prev_pixel;
            p01 <= pixel_in;
            p10 <= line_buf[x_cnt];
            p11 <= line_buf[x_cnt + 1];

            // 更新行缓存
            line_buf[x_cnt] <= pixel_in;

            // 保存当前像素
            prev_pixel <= pixel_in;

            // =============================
            // 插值计算（完全对应Python）
            // =============================
            if (x_phase == 0 && y_phase == 0)
                pixel_out <= p00;
            else if (x_phase == 1 && y_phase == 0)
                pixel_out <= (p00 + p01) >> 1;
            else if (x_phase == 0 && y_phase == 1)
                pixel_out <= (p00 + p10) >> 1;
            else
                pixel_out <= (p00 + p01 + p10 + p11) >> 2;

            valid_out <= 1'b1;

            // 相位控制
            x_phase <= ~x_phase;

            if (x_phase) begin
                x_cnt <= x_cnt + 1;
            end

            // 行结束（需要外部配合或增加行计数）
        end
        else begin
            valid_out <= 1'b0;
        end
    end

endmodule