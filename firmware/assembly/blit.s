
 push {r4,r5,r6,lr}
 mov r4,r9
 adds r5,r4,#1
 mov r9,r5
 mov r5,r8
 cmp r4,r5
 bne blit_done
 sub sp,#8
 ldr r4,[sp,#24]
 str r4,[sp]
 bl 0x7b82
 add sp,#8
blit_done:
 pop {r4,r5,r6,pc}
 .align 2
 marker: .word 0xdeadbeef
