
 push {r4,r5,r6,r7,lr}
 sub sp,#12
 cmp r0,#134
 bhs draw_done
 movs r1,#12
 muls r0,r1
 ldr r4,desc_base
 adds r4,r4,r0
 ldrh r0,[r4,#4]
 ldrh r1,[r4,#6]
 orrs r0,r1
 bne clear
 ldrh r0,[r4,#8]
 cmp r0,#240
 bne clear
 ldrh r0,[r4,#10]
 cmp r0,#135
 beq image
clear:
 movs r0,#134
 str r0,[sp]
 movs r0,#0
 movs r1,#0
 movs r2,#0
 movs r3,#239
 bl 0x27900
image:
 ldr r0,[r4]
 str r0,[sp]
 ldrh r0,[r4,#4]
 ldrh r1,[r4,#6]
 ldrh r2,[r4,#8]
 ldrh r3,[r4,#10]
 bl 0x27800
 draw_done:
 add sp,#12
 pop {r4,r5,r6,r7,pc}
 .align 2
 desc_base: .word 0x1d800
