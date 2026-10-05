/* Isolated actual-Tau-CPU command exercise; synthetic APF completion only. */
typedef unsigned int u32;
#define STATUS (*(volatile u32 *)0x80000030u)
#define EXIT (*(volatile u32 *)0x80000004u)
static void fail(u32 reason) { EXIT=reason; for (;;) {} }
int main(void) {
 for (u32 operation=0;operation<300;operation++) {
  u32 before=(STATUS>>8)&255;
  STATUS=operation%5;
  /* Attempt an extra GO only while the crossing owns the command. */
  u32 s=STATUS;
  if (!(s&1)) fail(1);
  STATUS=operation%5;
  u32 budget=20000;
  do { s=STATUS; if (!--budget) fail(2); } while (((s>>8)&255)==before);
  if (((s>>8)&255)!=((before+1)&255)) fail(3);
  if (((s>>2)&7)!=(operation&7)) fail(4);
  if ((s&3)!=2) fail(5);
 }
 EXIT=0;
 for (;;) {}
}
