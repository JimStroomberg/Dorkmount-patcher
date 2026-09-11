.syntax unified
.thumb
.cpu cortex-m4
.section .clock_entry,"ax",%progbits
.global clock_idle
.type clock_idle,%function
.thumb_func
clock_idle:
    bx lr
    nop
.size clock_idle, .-clock_idle
.section .dispatch_hook,"ax",%progbits
.global dispatch_hook
.type dispatch_hook,%function
.thumb_func
dispatch_hook:
    bl live_dispatch
.size dispatch_hook, .-dispatch_hook
