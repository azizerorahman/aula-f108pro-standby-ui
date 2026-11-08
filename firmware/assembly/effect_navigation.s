
 ldr r0,ui_slot
 ldrb r0,[r0]
 cmp r0,#20
 blo valid
 movs r0,#0
valid:
 ldr r1,raw_effect
 strb r0,[r1]
 bx lr
 .align 2
ui_slot: .word 0x20000236
raw_effect: .word 0x20000156


 push {r3,r4,r5,lr}
 ldr r0,effect_ptr
 ldrb r4,[r0]
 cmp r4,#20
 blo valid_effect
 movs r4,#0
valid_effect:
 ldr r0,ui_ptr
 strb r4,[r0]
 ldr r0,language_ptr
 ldrb r0,[r0]
 cmp r0,#0
 beq chinese
 ldr r0,english_page
 b store_page
chinese:
 ldr r0,chinese_page
store_page:
 ldr r1,page_ptr
 str r0,[r1]
 movs r0,#72
 bl 0x10030
 mov r0,r4
 movs r1,#3
 ands r0,r1
 adds r0,#29
 bl 0x10030
 pop {r3,r4,r5,pc}
 .align 2
effect_ptr: .word 0x20000156
ui_ptr: .word 0x20000236
language_ptr: .word 0x20000233
english_page: .word 0x240e30
chinese_page: .word 0xe0a9c
page_ptr: .word 0x20000214
