
 push {r4,r5,r6,lr}
 mov r4,r9
 adds r5,r4,#1
 mov r9,r5
 mov r5,r8
 cmp r4,r5
 bne fill_done
 cmp r0,#0
 bne fill_done
 mov r4,r1
 mov r5,r2
 subs r2,r3,r1
 adds r2,#1
 ldr r3,[sp,#16]
 subs r3,r3,r5
 adds r3,#1
 mov r0,r4
 mov r1,r5
 sub sp,#8
 ldr r4,black_source
 str r4,[sp]
 bl 0x7b82
 add sp,#8
fill_done:
 pop {r4,r5,r6,pc}
 .align 2
 marker: .word 0xdeadbeef
 black_source: .word 0x330100
