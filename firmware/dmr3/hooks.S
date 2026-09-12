/* SPDX-License-Identifier: GPL-3.0-only */
.syntax unified
.thumb
.cpu cortex-m4

.section .clock_entry,"ax",%progbits
    bx lr
    nop
.section .stopwatch_entry,"ax",%progbits
    bx lr
    nop
.section .timer_entry,"ax",%progbits
    movs r0, #0
    bx lr

/* The existing click handler already owns its stack and selected-view pointer. */
.section .app_entry,"ax",%progbits
    strh.w r4, [r8]
    bl dashboard_waiting
    b.w stock_click_return

.section .crop_hook,"ax",%progbits
    b.w dashboard_crop
.section .image_hook,"ax",%progbits
    b.w dashboard_image
.section .dispatch_hook,"ax",%progbits
    bl live_dispatch

/* Replay each replaced, position-independent prologue before its original body. */
.section .text.trampolines,"ax",%progbits
.global original_crop
.type original_crop,%function
.thumb_func
original_crop:
    push.w {r3, r4, r5, r6, r7, r8, r9, r10, r11, lr}
    b.w stock_crop_body
.size original_crop, .-original_crop
.global original_image
.type original_image,%function
.thumb_func
original_image:
    push.w {r0, r1, r4, r5, r6, r7, r8, r9, r10, r11, lr}
    b.w stock_image_body
.size original_image, .-original_image
