.section .text.start
.global _start
_start:
 li sp,0x3ee0
 li gp,0
 call main
1: j 1b
