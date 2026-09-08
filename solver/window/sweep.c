/* DP6: stream Bitcoin addresses on stdin, compute Electrum scripthash
 * (SHA256 of scriptPubKey), report those present in the ~20 BTC target set.
 * Handles P2PKH (1..), P2SH (3..) and bech32/bech32m (bc1..).            */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <openssl/sha.h>

/* ---------- target hash set: open addressing, full 32-byte keys ---------- */
static uint8_t *KEYS; static uint8_t *USED; static size_t CAP, NKEY;
static inline uint64_t k64(const uint8_t*h){ uint64_t v; memcpy(&v,h,8); return v; }
static void hs_init(size_t n){ CAP=1; while(CAP < n*4) CAP<<=1;
  KEYS=calloc(CAP,32); USED=calloc(CAP,1); if(!KEYS||!USED){fprintf(stderr,"oom\n");exit(1);} }
static void hs_add(const uint8_t*h){ size_t i=k64(h)&(CAP-1);
  while(USED[i]){ if(!memcmp(KEYS+i*32,h,32)) return; i=(i+1)&(CAP-1);} 
  USED[i]=1; memcpy(KEYS+i*32,h,32); NKEY++; }
static inline int hs_has(const uint8_t*h){ size_t i=k64(h)&(CAP-1);
  while(USED[i]){ if(!memcmp(KEYS+i*32,h,32)) return 1; i=(i+1)&(CAP-1);} return 0; }

/* ---------- base58 ---------- */
static int8_t B58[256];
static void b58_init(void){ const char*A="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  memset(B58,-1,256); for(int i=0;i<58;i++) B58[(uint8_t)A[i]]=i; }
static int b58dec25(const char*s,int len,uint8_t*out){ /* out[25] */
  uint8_t buf[25]; memset(buf,0,25);
  for(int i=0;i<len;i++){ int c=B58[(uint8_t)s[i]]; if(c<0) return -1;
    int carry=c;
    for(int j=24;j>=0;j--){ carry += 58*(int)buf[j]; buf[j]=(uint8_t)(carry&0xff); carry>>=8; }
    if(carry) return -1; }
  memcpy(out,buf,25); return 0; }

/* ---------- bech32 ---------- */
static const char*BCH="qpzry9x8gf2tvdw0s3jn54khce6mua7l";
static uint32_t bpolymod(const uint8_t*v,int n){ const uint32_t G[5]={0x3b6a57b2,0x26508e6d,0x1ea119fa,0x3d4233dd,0x2a1462b3};
  uint32_t c=1; for(int i=0;i<n;i++){ uint32_t b=c>>25; c=((c&0x1ffffff)<<5)^v[i];
    for(int k=0;k<5;k++) if((b>>k)&1) c^=G[k]; } return c; }
static int bech32_script(const char*a,int len,uint8_t*script,int*slen){
  char lo[128]; if(len>=128||len<8) return -1;
  for(int i=0;i<len;i++){ char c=a[i]; if(c>='A'&&c<='Z') c+=32; lo[i]=c; } lo[len]=0;
  int pos=-1; for(int i=len-1;i>=0;i--) if(lo[i]=='1'){pos=i;break;}
  if(pos<1||pos+7>len) return -1;
  uint8_t v[128]; int n=0;
  for(int i=0;i<pos;i++) v[n++]=(uint8_t)lo[i]>>5;
  v[n++]=0;
  for(int i=0;i<pos;i++) v[n++]=(uint8_t)lo[i]&31;
  int dstart=n;
  for(int i=pos+1;i<len;i++){ const char*p=strchr(BCH,lo[i]); if(!p) return -1; v[n++]=(uint8_t)(p-BCH); }
  uint32_t pm=bpolymod(v,n);
  if(pm!=1 && pm!=0x2bc830a3) return -1;
  int dn=n-dstart-6; if(dn<1) return -1;
  uint8_t*d=v+dstart; int witver=d[0];
  /* convertbits 5->8, no pad */
  uint8_t prog[64]; int pn=0; uint32_t acc=0; int bits=0;
  for(int i=1;i<dn;i++){ acc=(acc<<5)|d[i]; bits+=5;
    while(bits>=8){ bits-=8; if(pn>=64) return -1; prog[pn++]=(acc>>bits)&0xff; } }
  if(bits>=5) return -1;
  if(pn<2||pn>40) return -1;
  if(witver==0){ if(pn!=20&&pn!=32) return -1; script[0]=0x00; }
  else if(witver>=1&&witver<=16) script[0]=0x50+witver;
  else return -1;
  script[1]=(uint8_t)pn; memcpy(script+2,prog,pn); *slen=pn+2; return 0; }

int main(int argc,char**argv){
  if(argc<2){ fprintf(stderr,"usage: sweep targets.tsv < addrs\n"); return 2; }
  b58_init();
  /* load targets */
  FILE*tf=fopen(argv[1],"r"); if(!tf){perror("targets");return 2;}
  char line[512]; size_t cnt=0;
  while(fgets(line,sizeof line,tf)) cnt++;
  rewind(tf); hs_init(cnt?cnt:16);
  while(fgets(line,sizeof line,tf)){
    if(strlen(line)<64) continue;
    uint8_t h[32]; int ok=1;
    for(int i=0;i<32;i++){ unsigned x; if(sscanf(line+2*i,"%2x",&x)!=1){ok=0;break;} h[i]=(uint8_t)x; }
    if(ok) hs_add(h); }
  fclose(tf);
  fprintf(stderr,"targets loaded: %zu\n",NKEY);

  char buf[256]; uint8_t raw[25], script[64], sh[32];
  unsigned long long n=0,hits=0,bad=0;
  while(fgets(buf,sizeof buf,stdin)){
    int len=strlen(buf);
    while(len && (buf[len-1]=='\n'||buf[len-1]=='\r'||buf[len-1]==' ')) buf[--len]=0;
    if(len<10) continue;
    n++;
    int slen=0;
    if(buf[0]=='b'&&buf[1]=='c'&&buf[2]=='1'){
      if(bech32_script(buf,len,script,&slen)<0){ bad++; continue; }
    } else if(buf[0]=='1'||buf[0]=='3'){
      if(len>34+2 || b58dec25(buf,len,raw)<0){ bad++; continue; }
      if(raw[0]==0x00){ script[0]=0x76;script[1]=0xA9;script[2]=0x14;
        memcpy(script+3,raw+1,20); script[23]=0x88;script[24]=0xAC; slen=25; }
      else if(raw[0]==0x05){ script[0]=0xA9;script[1]=0x14;
        memcpy(script+2,raw+1,20); script[22]=0x87; slen=23; }
      else { bad++; continue; }
    } else { bad++; continue; }
    SHA256(script,slen,sh);
    if(hs_has(sh)){
      hits++;
      printf("%s\t",buf);
      for(int i=0;i<32;i++) printf("%02x",sh[i]);
      printf("\n"); fflush(stdout);
    }
  }
  fprintf(stderr,"scanned=%llu hits=%llu unparsed=%llu\n",n,hits,bad);
  return 0; }
