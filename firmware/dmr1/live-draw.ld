ENTRY(live_dispatch)
SECTIONS {
  . = 0x08009a60;
  .clock_entry : { *(.clock_entry) }
  . = 0x08009a64;
  .text : { *(.text.live_dispatch) *(.text*) *(.rodata*) }
  ASSERT(. <= 0x08009bb8, "Handler exceeds original Clock function body")
  . = 0x0800c058;
  .dispatch_hook : { *(.dispatch_hook) }
  /DISCARD/ : { *(.ARM.attributes) *(.ARM.exidx*) *(.comment) *(.note*) }
}
stock_dispatch = 0x0800b415;
stock_reply = 0x0800c88d;
stock_rectangle = 0x0800b09d;
stock_window = 0x080087e1;
stock_data = 0x08008d45;
ASSERT(SIZEOF(.clock_entry) == 4, "Unexpected Clock entry patch size")
ASSERT(SIZEOF(.dispatch_hook) == 4, "Unexpected dispatcher hook size")
