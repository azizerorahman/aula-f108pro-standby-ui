
 push {r4,r5,r6,r7,lr}
 sub sp,#20
 str r0,[sp,#4]
 cmp r0,#78
 bne test_time_event
 movs r0,#1
 bl 0x1b000
 b clock_done
test_time_event:
 cmp r0,#76
 blo other_event
 cmp r0,#77
 bhi other_event
 movs r0,#0
 bl 0x1b000
 b clock_done
other_event:
 cmp r0,#72
 bne top_status
 movs r0,#134
 str r0,[sp]
 movs r0,#0
 movs r1,#0
 movs r2,#0
 movs r3,#239
 bl 0x7b20
 movs r0,#0
 bl 0x1b000
top_status:
 movs r0,#29
 str r0,[sp]
 movs r0,#0
 movs r1,#0
 movs r2,#0
 movs r3,#239
 bl 0x7b20
 ldr r0,language_ptr
 ldrb r4,[r0]
 cmp r4,#0
 beq language_valid
 movs r4,#1
language_valid:
 ldr r0,flags_ptr
 ldr r5,[r0]
 ldr r6,time_ptr
 ldrb r0,[r6,#1]
 cmp r0,#1
 blo invalid_month
 cmp r0,#12
 bls month_valid
invalid_month:
 movs r0,#1
month_valid:
 subs r0,#1
 movs r1,#31
 muls r0,r1
 ldrb r1,[r6,#3]
 cmp r1,#1
 blo invalid_day
 cmp r1,#31
 bls day_valid
invalid_day:
 movs r1,#1
day_valid:
 subs r1,#1
 adds r0,r0,r1
 str r0,[sp,#8]
 ldrb r7,[r6,#2]
 cmp r7,#7
 blo weekday_valid
 movs r7,#0
weekday_valid:
 cmp r4,#0
 beq chinese_date
 ldr r0,weekday_en_base
 adds r0,r0,r7
 movs r1,#0
 bl 124416
 ldr r0,weekday_en_widths
 lsls r1,r7,#1
 ldrh r1,[r0,r1]
 adds r1,#6
 ldr r0,[sp,#8]
 ldr r2,date_en_base
 adds r0,r0,r2
 bl 124416
 b battery
chinese_date:
 ldr r0,[sp,#8]
 movs r1,#0
 bl 124416
 ldr r0,date_cn_widths
 ldr r1,[sp,#8]
 lsls r1,r1,#1
 ldrh r1,[r0,r1]
 adds r1,#6
 ldr r0,weekday_cn_base
 adds r0,r0,r7
 bl 124416
battery:
 ldr r0,battery_ptr
 ldrb r0,[r0]
 cmp r0,#100
 bls pct_valid
 movs r0,#100
pct_valid:
 ldr r1,charging_ptr
 ldrb r1,[r1]
 cmp r1,#0
 beq no_charge
 adds r0,#101
no_charge:
 ldr r1,battery_base
 adds r0,r0,r1
 movs r1,#0
 bl 124416
 movs r0,#2
 tst r0,r5
 beq bottom
 ldr r0,caps_base
 adds r0,r0,r4
 movs r1,#0
 bl 124416
bottom:
 movs r0,#134
 str r0,[sp]
 movs r0,#0
 movs r1,#0
 movs r2,#105
 movs r3,#239
 bl 0x7b20
 ldr r0,mode_ptr
 ldrb r0,[r0]
 movs r6,#0
 cmp r0,#2
 beq radio_mode
 cmp r0,#1
 bne mode_done
 ldr r0,channel_ptr
 ldrb r0,[r0]
 movs r6,#2
 cmp r0,#2
 bne not_bt2
 movs r6,#3
not_bt2:
 cmp r0,#4
 bne mode_done
 movs r6,#4
 b mode_done
radio_mode:
 movs r6,#1
mode_done:
 movs r0,#5
 muls r0,r4
 adds r0,r0,r6
 lsls r0,r0,#2
 movs r1,#1
 ands r1,r5
 adds r0,r0,r1
 movs r1,#8
 ands r1,r5
 lsrs r1,r1,#2
 adds r0,r0,r1
 ldr r1,bottom_base
 adds r0,r0,r1
 movs r1,#0
 bl 124416
 ldr r0,os_ptr
 ldrb r0,[r0]
 cmp r0,#4
 blo os_valid
 movs r0,#0
os_valid:
 ldr r1,os_base
 adds r0,r0,r1
 movs r1,#0
 bl 124416
 b clock_done
seconds_only:
 movs r0,#1
 bl 0x1b000
 b clock_done
time_only:
 movs r0,#0
 bl 0x1b000
clock_done:
 add sp,#20
 pop {r4,r5,r6,r7,pc}
 .align 2
language_ptr: .word 0x20000233
flags_ptr: .word 0x20000184
time_ptr: .word 0x2000021c
battery_ptr: .word 0x200000f6
charging_ptr: .word 0x2000005b
mode_ptr: .word 0x200000e7
channel_ptr: .word 0x200000e8
os_ptr: .word 0x20000050
date_cn_widths: .word 126976
weekday_en_widths: .word 127720
date_en_base: .word 372
weekday_cn_base: .word 744
weekday_en_base: .word 751
battery_base: .word 758
caps_base: .word 960
bottom_base: .word 962
os_base: .word 1002


 push {r4,r5,r6,r7,lr}
 sub sp,#12
 mov r5,r1
 movs r1,#12
 muls r0,r1
 ldr r4,part_descriptors
 adds r4,r4,r0
 ldr r0,[r4]
 str r0,[sp]
 ldrh r0,[r4,#4]
 adds r0,r0,r5
 ldrh r1,[r4,#6]
 ldrh r2,[r4,#8]
 ldrh r3,[r4,#10]
 bl 0x7b82
 add sp,#12
 pop {r4,r5,r6,r7,pc}
 .align 2
part_descriptors: .word 139264
