/* SPDX-License-Identifier: GPL-3.0-only
 * Original Dashboard artwork and view hooks for exact Dock 1.29.0 only.
 * Existing image storage is read normally and never modified.
 */
typedef unsigned char u8;
typedef unsigned int u32;

extern void stock_rectangle(u32, u32, u32, u32, u32);
extern void stock_text(u32, u32, u32, u32, const char *, u32, u32);
extern void stock_clear(u32);
extern void stock_reset_clock(void);
extern void original_image(u32, u32);
extern void original_crop(u32, u32, u32, u32, u32, u32, u32);

__attribute__((section(".text.dashboard_tile")))
static void tile(u32 rgb, u32 background) {
    /* A monitor with three dashboard bars. Coordinates are in the first tile. */
    static const u8 rectangles[][4] = {
        {26, 36, 68, 44}, {30, 40, 60, 36},
        {37, 61, 10, 10}, {55, 52, 10, 19}, {73, 45, 10, 26},
        {49, 80, 22, 4}, {43, 84, 34, 3},
    };
    u32 foreground = ((rgb & 0xf8) << 8) | ((rgb >> 5) & 0x7e0) |
                     ((rgb >> 19) & 0x1f);
    stock_rectangle(10, 20, 100, 90, background);
    for (u32 i = 0; i < sizeof rectangles / sizeof rectangles[0]; i++) {
        const u8 *r = rectangles[i];
        stock_rectangle(r[0], r[1], r[2], r[3], i == 1 ? background : foreground);
    }
}

__attribute__((section(".text.dashboard_crop")))
void dashboard_crop(u32 x, u32 y, u32 w, u32 h,
                    u32 rgb, u32 background, u32 image) {
    if (image == 0x25800) return; /* Suppress old Clock controls on accent updates. */
    if (image == 0 && x == 10 && y == 20 && w == 100 && h == 90)
        tile(rgb, background);
    else
        original_crop(x, y, w, h, rgb, background, image);
}

__attribute__((section(".text.dashboard_image")))
void dashboard_image(u32 image, u32 mode) {
    if (image == 0x25800) return;
    original_image(image, mode);
    if (image == 0)
        tile(*(const u32 *)0x08010464, 0);
}

__attribute__((section(".text.dashboard_waiting")))
void dashboard_waiting(void) {
    stock_reset_clock();
    stock_clear(0);
    stock_text(40, 96, 0, 0xffff, "Waiting...", 48, 10);
}
