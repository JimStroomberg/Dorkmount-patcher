ENTRY(live_dispatch)
SECTIONS {
  . = 0x08009690;
  .crop_hook : { *(.crop_hook) }
  . = 0x080097ea;
  .app_entry : { *(.app_entry) }
  ASSERT(. <= 0x080097f8, "Dashboard entry exceeds old Clock entry prefix")
  . = 0x080097f8;
  .image : { *(.text.dashboard_image) }
  ASSERT(. <= 0x0800982e, "Image wrapper exceeds replaced Clock entry body")
  . = 0x08009938;
  .stopwatch_entry : { *(.stopwatch_entry) }
  .waiting : { *(.text.dashboard_waiting) *(.rodata.str1.1) }
  ASSERT(. <= 0x080099a0, "Waiting view exceeds original stopwatch renderer")
  . = 0x08009a60;
  .clock_entry : { *(.clock_entry) }
  .draw : { *(.text.live_dispatch) *(.rodata.live_dispatch*) }
  ASSERT(. <= 0x08009bb8, "Drawing handler exceeds original Clock renderer")
  . = 0x0800a470;
  .timer_entry : { *(.timer_entry) }
  .dashboard : {
    *(.text.dashboard_tile) *(.text.dashboard_crop) *(.text.trampolines)
    *(.rodata*)
  }
  ASSERT(. <= 0x0800a5ac, "Dashboard exceeds original timer editor")
  . = 0x0800b1cc;
  .image_hook : { *(.image_hook) }
  . = 0x0800c058;
  .dispatch_hook : { *(.dispatch_hook) }
  .unexpected : { *(.text*) *(.data*) *(.bss*) }
  ASSERT(SIZEOF(.unexpected) == 0, "Unexpected code or mutable data")
  /DISCARD/ : { *(.ARM.attributes) *(.ARM.exidx*) *(.comment) *(.note*) }
}
stock_dispatch = 0x0800b415;
stock_reply = 0x0800c88d;
stock_rectangle = 0x0800b09d;
stock_window = 0x080087e1;
stock_data = 0x08008d45;
stock_text = 0x08008e91;
stock_clear = 0x08008375;
stock_reset_clock = 0x08009a49;
stock_click_return = 0x08009781;
stock_crop_body = 0x08009695;
stock_image_body = 0x0800b1d1;
ASSERT(SIZEOF(.crop_hook) == 4, "Unexpected crop hook size")
ASSERT(SIZEOF(.image_hook) == 4, "Unexpected image hook size")
ASSERT(SIZEOF(.dispatch_hook) == 4, "Unexpected dispatcher hook size")
ASSERT(SIZEOF(.clock_entry) == 4, "Unexpected Clock entry size")
ASSERT(SIZEOF(.stopwatch_entry) == 4, "Unexpected stopwatch entry size")
ASSERT(SIZEOF(.timer_entry) == 4, "Unexpected timer entry size")
