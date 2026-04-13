module isp_top #(
    parameter IMG_WIDTH = 640
)(
    input  wire        clk,
    input  wire        rst_n,

    input  wire [7:0]  pixel_in,
    input  wire        valid_in,

    input  wire        scale_mode,   // 0: downscale, 1: upscale

    output wire [7:0]  pixel_out,
    output wire        valid_out
);

    // ============================================================
    // Stage 1: 暗光增强
    // ============================================================
    wire [7:0] dark_pixel;
    wire       dark_valid;

    dark_enhance_lut u_dark (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(pixel_in),
        .valid_in(valid_in),
        .pixel_out(dark_pixel),
        .valid_out(dark_valid)
    );

    // ============================================================
    // Stage 2: 引导滤波
    // ============================================================
    wire [7:0] gf_pixel;
    wire       gf_valid;

    guided_filter_3x3 #(
        .IMG_WIDTH(IMG_WIDTH),
        .THRESHOLD(8'd20)
    ) u_gf (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(dark_pixel),
        .valid_in(dark_valid),
        .pixel_out(gf_pixel),
        .valid_out(gf_valid)
    );

    // ============================================================
    // Stage 3: HDR增强
    // ============================================================
    wire [7:0] hdr_pixel;
    wire       hdr_valid;

    hdr_lut u_hdr (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(gf_pixel),
        .valid_in(gf_valid),
        .pixel_out(hdr_pixel),
        .valid_out(hdr_valid)
    );

    // ============================================================
    // Stage 4: 缩放模块
    // ============================================================
    wire [7:0] up_pixel, down_pixel;
    wire       up_valid, down_valid;

    upscale_x2 u_up (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(hdr_pixel),
        .valid_in(hdr_valid),
        .pixel_out(up_pixel),
        .valid_out(up_valid)
    );

    downscale_x2 u_down (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(hdr_pixel),
        .valid_in(hdr_valid),
        .pixel_out(down_pixel),
        .valid_out(down_valid)
    );

    // ============================================================
    // 输出选择
    // ============================================================
    assign pixel_out = scale_mode ? up_pixel : down_pixel;
    assign valid_out = scale_mode ? up_valid : down_valid;

endmodule