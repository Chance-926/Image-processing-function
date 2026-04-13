module downscale_x2 (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  pixel_in,
    input  wire        valid_in,

    output reg  [7:0]  pixel_out,
    output reg         valid_out
);

    // 行缓存
    reg [7:0] line_buf [0:1023];
    reg [10:0] x_cnt;

    reg [7:0] p00, p01, p10, p11;
    reg [7:0] prev_pixel;

    reg phase_x;
    reg phase_y;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            x_cnt <= 0;
            valid_out <= 0;
            phase_x <= 0;
            phase_y <= 0;
        end
        else if (valid_in) begin

            // 获取2×2窗口
            p00 <= prev_pixel;
            p01 <= pixel_in;
            p10 <= line_buf[x_cnt];
            p11 <= line_buf[x_cnt + 1];

            line_buf[x_cnt] <= pixel_in;
            prev_pixel <= pixel_in;

            // 每2×2输出一个像素
            if (phase_x == 1 && phase_y == 1) begin
                pixel_out <= (p00 + p01 + p10 + p11) >> 2;
                valid_out <= 1'b1;
            end
            else begin
                valid_out <= 1'b0;
            end

            // 相位更新
            phase_x <= ~phase_x;

            if (phase_x) begin
                x_cnt <= x_cnt + 1;
            end

        end
        else begin
            valid_out <= 0;
        end
    end

endmodule