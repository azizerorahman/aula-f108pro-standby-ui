
 push {r0,r1,r2,r3,r4,r5,r6,r7,lr}
 sub sp,#20
 mov r0,r8
 str r0,[sp,#4]
 mov r0,r9
 str r0,[sp,#8]
 movs r0,#0
 mov r8,r0
 mov r9,r0
 cmp r7,#104
 bne fresh_event
 ldr r0,queue_state
 ldrb r1,[r0,#3]
 ldrb r2,[r0,#2]
 subs r2,r2,r1
 bpl continuation_size
 adds r2,#100
continuation_size:
 cmp r2,#2
 bhs continuation_valid
 b done
continuation_valid:
 ldr r3,queue_data
 ldrb r7,[r3,r1]
 adds r1,#1
 cmp r1,#100
 blo continuation_step
 movs r1,#0
continuation_step:
 ldrb r2,[r3,r1]
 mov r8,r2
 adds r1,#1
 cmp r1,#100
 blo continuation_commit
 movs r1,#0
continuation_commit:
 strb r1,[r0,#3]
 cmp r2,#1
 bhs step_lower_valid
 b done
step_lower_valid:
 cmp r2,#31
 bls fresh_event
 b done
fresh_event:
 cmp r7,#103
 bls event_valid
 b done
event_valid:
 # Need three free queue slots for an atomic continuation packet. If congested,
 # skip drawing instead of clearing half a frame or overwriting queued events.
 ldr r0,queue_state
 ldrb r1,[r0,#3]
 ldrb r2,[r0,#2]
 subs r1,r1,r2
 subs r1,#1
 bpl free_count
 adds r1,#100
free_count:
 cmp r1,#3
 bhs room_valid
 b done
room_valid:
 ldr r0,mode_pointer
 ldrb r0,[r0]
 cmp r0,#1
 bne after_clock
 ldr r0,clock_event_mask
 ldrb r0,[r0,r7]
 cmp r0,#0
 beq after_clock
 mov r0,r7
 cmp r0,#0
 bne clock_call
 movs r0,#72
clock_call:
 bl 0x1e000
 b completed
after_clock:
 ldr r0,direct_table
 lsls r1,r7,#1
 ldrh r0,[r0,r1]
 cmp r0,#0
 beq not_direct
 subs r0,#1
 b render
not_direct:
 cmp r7,#93
 blo pointer_route
 cmp r7,#96
 bhi pointer_route
 movs r0,#92
 cmp r7,#93
 bne not_up
 movs r0,#93
 b render
not_up:
 cmp r7,#94
 bne render
 movs r0,#91
 b render
pointer_route:
 ldr r0,event_mask
 ldrb r0,[r0,r7]
 cmp r0,#0
 bne route_allowed
 b done
route_allowed:
 ldr r0,current_pointer
 ldr r6,[r0]
 ldr r4,row_base
 movs r5,#43
row_loop:
 ldr r0,[r4]
 cmp r0,r6
 beq row_match
 adds r4,#16
 subs r5,#1
 bne row_loop
 # Full boot/custom-animation frames retain their native raw layout.
 cmp r7,#72
 beq raw_range
 b done
raw_range:
 ldr r0,boot_start
 cmp r6,r0
 blo test_custom
 ldr r0,boot_end
 cmp r6,r0
 blo raw_draw
test_custom:
 ldr r0,custom_start
 cmp r6,r0
 bhs custom_lower
 b done
custom_lower:
 ldr r0,custom_last
 cmp r6,r0
 bls raw_draw
 b done
raw_draw:
 mov r0,r8
 cmp r0,#0
 beq raw_valid
 b done
raw_valid:
 sub sp,#8
 str r6,[sp]
 movs r0,#0
 movs r1,#0
 movs r2,#240
 movs r3,#135
 bl 0x7b82
 add sp,#8
 b done
row_match:
 ldr r0,[r4,#4]
 movs r1,#0
 cmp r0,#0
 beq option_index
 ldrb r1,[r0]
option_index:
 ldr r2,[r4,#12]
 cmp r1,r2
 blo option_valid
 b done
option_valid:
 ldr r0,[r4,#8]
 lsls r1,r1,#1
 ldrh r0,[r0,r1]
render:
 bl 0x1b400
completed:
 mov r0,r8
 adds r0,#1
 mov r1,r9
 cmp r0,r1
 blo more_operations
 b done
more_operations:
 # Recheck capacity and prepend atomically; preserve the incoming IRQ mask.
 cmp r0,#31
 bls stage_valid
 b done
stage_valid:
 .byte 0xef,0xf3,0x10,0x82
 str r2,[sp,#12]
 cpsid i
 ldr r4,queue_state
 ldrb r1,[r4,#3]
 ldrb r2,[r4,#2]
 subs r1,r1,r2
 subs r1,#1
 bpl prepend_free
 adds r1,#100
prepend_free:
 cmp r1,#3
 blo prepend_done
 ldrb r5,[r4,#3]
 subs r5,#3
 bpl prepend_index
 adds r5,#100
prepend_index:
 mov r6,r5
 ldr r3,queue_data
 movs r1,#104
 strb r1,[r3,r5]
 adds r5,#1
 cmp r5,#100
 blo prepend_original
 movs r5,#0
prepend_original:
 strb r7,[r3,r5]
 adds r5,#1
 cmp r5,#100
 blo prepend_stage
 movs r5,#0
prepend_stage:
 strb r0,[r3,r5]
 strb r6,[r4,#3]
prepend_done:
 ldr r2,[sp,#12]
 .byte 0x82,0xf3,0x10,0x88
done:
 mov r0,r8
 # Restore all high registers before returning into the OEM epilogue.
 ldr r0,[sp,#4]
 mov r8,r0
 ldr r0,[sp,#8]
 mov r9,r0
 ldr r0,exit_ptr
 str r0,[sp,#52]
 add sp,#20
 pop {r0,r1,r2,r3,r4,r5,r6,r7,pc}
 .align 2
 marker: .word 0xdeadbeef
 queue_state: .word 0x2000020c
 queue_data: .word 0x200020c7
 mode_pointer: .word 0x20000232
 current_pointer: .word 0x20000214
 clock_event_mask: .word 0x1f800
 direct_table: .word 120424
 event_mask: .word 120320
 row_base: .word 114688
 exit_ptr: .word 0xf269
 boot_start: .word 0x330100
 boot_end: .word 4638592
 custom_start: .word 0x740100
 custom_last: .word 16712416
