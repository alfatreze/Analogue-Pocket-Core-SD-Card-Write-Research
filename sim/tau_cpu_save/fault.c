/* CPU prototype only: same SDR5 record, modeled bounded APF transport. */
typedef unsigned int u32;
typedef unsigned long long u64;
#define REGS ((volatile u32 *)0x80000000u)
#define TX ((volatile u32 *)0x80010000u)
#define RX ((volatile u32 *)0x80018000u)
static unsigned char records[2][512];
static void finish(u32 code) { REGS[1]=code;for (;;) {} }
static u32 be32(const unsigned char *p) { return ((u32)p[0]<<24)|((u32)p[1]<<16)|((u32)p[2]<<8)|p[3]; }
static void put32(unsigned char *p,u32 v) { p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v; }
static u32 crc(const unsigned char *p) {
 u32 c=~0u;
 for(u32 i=0;i<512;i++)if(i<28||i>=32) {
  c^=p[i];for(u32 bit=0;bit<8;bit++)c=(c>>1)^((0u-(c&1u))&0xedb88320u);
 }
 return ~c;
}
static u64 valid(const unsigned char *p) {
 if(be32(p)!=0x53445235u||be32(p+4)!=0x00010020u||be32(p+8)!=512||be32(p+20)!=480||be32(p+24)!=0||be32(p+28)!=crc(p))return 0;
 return ((u64)be32(p+12)<<32)|be32(p+16);
}
static void target(u32 command,u32 slot,u32 offset,u32 bridge,u32 length) {
 REGS[8]=slot;REGS[9]=offset;REGS[10]=bridge;REGS[11]=length;
 __asm__ volatile("fence iorw,iorw" ::: "memory");
 u32 before=(REGS[12]>>8)&255;REGS[12]=command;
 u32 budget=500,s;
 do {s=REGS[12];if(!--budget)finish(0x20);}while(((s>>8)&255)==before);
 if((s&3)!=2||((s>>2)&7)!=0||((s>>8)&255)!=((before+1)&255))finish(0x21);
}
static void read_file(u32 slot,unsigned char *record) {
 target(0,0x25+slot,0,0x21000000u,8192);
 for(u32 w=0;w<2048;w++) {
  u32 value=RX[w];
  if(w<128||w>=256) {if(value!=0xa5a5a5a5u)finish(0x25);}
  else put32(record+(w-128)*4,value);
 }
}
static int blank(const unsigned char *p) {for(u32 i=0;i<512;i++)if(p[i]!=0xa5)return 0;return 1;}
static void generate(unsigned char *p,u64 g) {
 put32(p,0x53445235u);put32(p+4,0x00010020u);put32(p+8,512);put32(p+12,g>>32);put32(p+16,g);put32(p+20,480);put32(p+24,0);
 for(u32 i=0;i<480;i++)p[32+i]=(i^(i>>8)^(u32)g^((u32)g>>8)^0x5b)&255;
 put32(p+28,crc(p));
}
int main(void) {
 read_file(0,records[0]);read_file(1,records[1]);
 for(u32 save=0;save<4;save++) {
  u64 a=valid(records[0]),b=valid(records[1]);
  if(a&&a==b)for(u32 i=0;i<512;i++)if(records[0][i]!=records[1][i])finish(0x11);
  if(!a&&!b&&(!blank(records[0])||!blank(records[1])))finish(0x13);
  u64 latest=a>=b?a:b;if(latest==~(u64)0)finish(0x12);
  u32 dest=(!a&&!b)?0:(a>=b?1:0);generate(records[dest],latest+1);
  for(u32 w=0;w<128;w++)TX[w]=be32(records[dest]+w*4);
  __asm__ volatile("fence iorw,iorw" ::: "memory");
  for(u32 chunk=0;chunk<4;chunk++)target(3,0x25+dest,512+chunk*128,0x20000000u+chunk*128,128);
  target(0,0x25+dest,0,0x21000000u,8192);
  for(u32 w=0;w<2048;w++) {
   u32 value=RX[w];if(w<128||w>=256){if(value!=0xa5a5a5a5u)finish(0x25);}
   else if(value!=be32(records[dest]+(w-128)*4))finish(0x22);
  }
 }
 finish(0);return 0;
}
