// CPU supervises B007 only; no payload pointers, APF registers, or file creation.
typedef unsigned int u32;
#define REG(n) (*(volatile u32 *)(0x80010000u+(n)))
static void fault(u32 code){REG(0x5c)=code;for(;;){}}
static u32 cmd(u32 n){
 for(u32 i=0;REG(4)&1;i++)if(i==100000)fault(1);
 u32 seq=REG(8);REG(0)=n;
 if(REG(0x24))fault(2);
 for(u32 i=0;i<100000;i++)if(REG(8)!=seq){u32 result=REG(12);REG(0x44)=result;return result;}
 fault(3);return 99;
}
void main(void){
 REG(0x40)=0;REG(0x50)=0;
 // A pending message and active engine survive CPU-only reset.
 while(REG(4)&1){}
 for(;;){
  cmd(4);u32 flags=REG(16);REG(0x48)=flags;
  if(flags&1024)break; // fault is observed without any recovery or retry
  if(flags&256){if(cmd(5)==0)break;}
 }
 u32 previous=REG(0x30),heartbeat=0;
 REG(0x50)=1;
 for(;;){
  cmd(4);u32 flags=REG(16);REG(0x48)=flags;
  u32 keys=REG(0x30),edges=keys&~previous;previous=keys;
  // B while writing means STOP; B while idle means cold read. Never retry fault.
  if(!(REG(4)&2) && !(flags&1024)){
   u32 status=flags&15;
   if(edges&32){if(status==8||status==2)cmd(3);else if(flags&256)cmd(1);}
   else if((edges&16)&&(flags&256))cmd(2);
  }
  REG(0x40)=++heartbeat;
 }
}
