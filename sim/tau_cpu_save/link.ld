OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
 . = 0;
 .text : { *(.text.start) *(.text*) }
 .rodata : { *(.rodata*) }
 .data : { *(.data*) }
 .bss : { *(.bss*) *(COMMON) }
}
