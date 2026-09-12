"""Draw three bands using only volatile DirectDraw commands. No firmware writes."""

from dorkmount_patcher.directdraw import open_keyboard

with open_keyboard() as screen:
    if not screen.capabilities()["selected"]:
        raise SystemExit("Select Dashboard (Clock on older patches), then run this example again.")
    screen.fill(0, 0, 320, 240, 0x0000)
    for y, color in [(30, 0xF800), (95, 0x07E0), (160, 0x001F)]:
        screen.fill(20, y, 280, 45, color)
print("Drawing acknowledged. The screen should show red, green and blue bands.")
