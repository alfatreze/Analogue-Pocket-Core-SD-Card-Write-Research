typedef unsigned int u32;
#define REG(n) (*(volatile u32 *)(0x80010000u+(n)))
#define EXIT (*(volatile u32 *)0x80020000u)
#define COOKIE (*(volatile u32 *)0x80003ff0u)
static void fail(u32 n){EXIT=n;for(;;){}}
static void check(int yes,u32 n){if(!yes)fail(n);}
static u32 cmd(u32 n){
 u32 seq=REG(8); REG(0)=n;
 for(u32 i=0;i<2000000;i++)if(REG(8)!=seq)return REG(12);
 fail(101);return 99;
}
static u32 flags(void){check(cmd(4)==0,102);return REG(16);}
static void wait_status(u32 n){for(u32 i=0;i<2000000;i++)if((flags()&15)==n)return;fail(103);}
void main(void){
 if(COOKIE==0x8008 && (PROFILE==5 || PROFILE==6 || PROFILE==7 || PROFILE==10)){
  check(REG(4)&2,110);
  u32 before=REG(28);REG(0)=2;check(REG(28)==before+1 && REG(36)==2,111);
  if(PROFILE==10){wait_status(7);check(cmd(5)==5,112);EXIT=0;return;}
  for(u32 i=0;i<2000000;i++){if(flags()&256)break;if(i==1999999)fail(113);}
  check(cmd(5)==0,114);check(!(REG(4)&2),115);
  check(cmd(1)==0,116);wait_status(5);EXIT=0;return;
 }
 COOKIE=0x8008;
 for(u32 i=0;i<2000000;i++){if(flags()&256)break;if(i==1999999)fail(117);}
 check(cmd(5)==0,118);check(cmd(2)==3,119);check(cmd(7)==1,120);
 check(cmd(1)==0,121);
 if(PROFILE==7){wait_status(5);fail(122);}
 if(PROFILE==1 || PROFILE==4 || PROFILE==9){wait_status(6);check(cmd(2)==5,123);EXIT=0;return;}
 wait_status(5);
 if(PROFILE==5){(*(volatile u32 *)0x80020004u)=1;for(;;){}}
 check(cmd(2)==0,124);
 if(PROFILE==6 || PROFILE==10){for(;;){flags();}}
 if(PROFILE==2){wait_status(6);check(cmd(5)==5,125);EXIT=0;return;}
 if(PROFILE==3){wait_status(7);check(cmd(5)==5,126);check(cmd(2)==5,127);EXIT=0;return;}
 check(cmd(1)==2,128);check(cmd(3)==0,129);wait_status(4);
 check(REG(20)==1,130);check(cmd(1)==0,131);wait_status(5);check(REG(24)==1,132);
 EXIT=0;
}
