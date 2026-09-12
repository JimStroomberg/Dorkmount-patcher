/* Experimental, stateless drawing endpoint. OFFLINE until separately packaged.
 * Reuses the current QLink receive buffer and original LCD/reply routines.
 * No globals, heap, flash operations or assembly buffer.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

extern void stock_dispatch(u32 command);
extern void stock_reply(u32 length, const void *payload, u32 status);
extern void stock_rectangle(u32 x, u32 y, u32 width, u32 height, u32 color);
extern void stock_window(u32 x, u32 y, u32 right, u32 bottom);
extern void stock_data(u32 value);

static u32 read16(const u8 *p) { return p[0] | ((u32)p[1] << 8); }

__attribute__((section(".text.live_dispatch")))
void live_dispatch(u32 command) {
    if (command != 0) { stock_dispatch(command); return; }
    const u8 *f = (const u8 *)0x200046ac;
    u32 length = f[0];
    if (length < 11 || length > 61 || f[1] ||
        f[7] != 'D' || f[8] != 'M' || f[9] != 'R' || f[10] != 1)
        goto bad;
    u32 selected = *(volatile u16 *)0x200000f2 == 1;
    if (f[11] == 0 && length == 11) {
        u8 caps[12] = {'D','M','R',3, 0x40,1, 0xf0,0, 21,0, 0,0x10};
        caps[9] = selected;
        stock_reply(sizeof caps, caps, 0);
        return;
    }
    if (!selected) { stock_reply(0, 0, 10); return; }
    if (length < 21) goto bad;
    u32 x=read16(f+12), y=read16(f+14), w=read16(f+16), h=read16(f+18);
    if (!w || !h || x+w > 320 || y+h > 240) goto bad;
    if (f[11] == 1 && length == 21 && w*h <= 4096) {
        stock_rectangle(x,y,w,h,read16(f+20));
    } else if (f[11] == 2 && w*h <= 21 && length == 19+2*w*h) {
        stock_window(x,y,x+w-1,y+h-1);
        for (u32 i=0; i<2*w*h; i+=2) {
            stock_data(f[21+i]);
            stock_data(f[20+i]);
        }
    } else goto bad;
    stock_reply(0,0,0);
    return;
bad:
    stock_reply(0,0,3);
}
