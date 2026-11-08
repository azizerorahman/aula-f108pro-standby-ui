// Device transport for the approved F108Pro Standby build.
// MCU packet sequence derived from the factory updater's selected 407CA0 workflow.
// SPI transport informed by AuRoN89's CC-BY-4.0 flasher; adapted with strict I/O and ACK checks.
using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Threading;
using Microsoft.Win32.SafeHandles;
public static class StandbyTransport {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFile(string n,uint a,uint s,IntPtr p,uint d,uint f,IntPtr t);
 [DllImport("hid.dll",SetLastError=true)][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_SetFeature(SafeFileHandle h,byte[] b,int n);
 [DllImport("hid.dll",SetLastError=true)][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_GetFeature(SafeFileHandle h,byte[] b,int n);
 [DllImport("hid.dll")][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_GetAttributes(SafeFileHandle h,ref ATTR a);
 [DllImport("hid.dll")][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_GetPreparsedData(SafeFileHandle h,out IntPtr p);
 [DllImport("hid.dll")][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_FreePreparsedData(IntPtr p);
 [DllImport("hid.dll")] static extern int HidP_GetCaps(IntPtr p,out CAPS c);
 [DllImport("hid.dll",SetLastError=true)][return:MarshalAs(UnmanagedType.U1)] static extern bool HidD_FlushQueue(SafeFileHandle h);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadFile(SafeFileHandle h,IntPtr b,uint n,IntPtr count,IntPtr ov);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool WriteFile(SafeFileHandle h,IntPtr b,uint n,IntPtr count,IntPtr ov);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetOverlappedResult(SafeFileHandle h,IntPtr ov,out uint n,bool wait);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CancelIoEx(SafeFileHandle h,IntPtr ov);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateEvent(IntPtr a,bool manual,bool state,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr e,uint ms);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [StructLayout(LayoutKind.Sequential)] struct ATTR {public int Size;public ushort VendorID,ProductID,VersionNumber;}
 [StructLayout(LayoutKind.Sequential)] struct CAPS {
  public ushort Usage,UsagePage,InputReportByteLength,OutputReportByteLength,FeatureReportByteLength;
  [MarshalAs(UnmanagedType.ByValArray,SizeConst=17)] public ushort[] Reserved;
  public ushort Link,IB,IV,ID,OB,OV,OD,FB,FV,FD;
 }
 [StructLayout(LayoutKind.Sequential)] struct OVERLAPPED {
  public IntPtr Internal,InternalHigh; public uint Offset,OffsetHigh; public IntPtr Event;
 }
 public sealed class Evidence {
  public string phase="not_started",error,chip_id,options,firmware_sha256,graphics_sha256;
  public int mcu_packets,mcu_bytes,graphics_pages,graphics_bytes;
  public bool mcu_mutation_started,mcu_checksum_verified,mcu_return_sent,graphics_begin,graphics_apply_verified,graphics_finalize_verified;
  public int mcu_checksum,expected_checksum;
  public List<string> events=new List<string>();
 }
 public static Evidence Current=new Evidence();
 public static Action<Evidence> Progress;
 public static string Hex(byte[] a){return BitConverter.ToString(a).Replace("-","").ToLowerInvariant();}
 static MockState mock;
 static void Pause(int ms){if(mock==null)Thread.Sleep(ms);}
 sealed class MockState {
  public string fault,phase="idle";public byte[] last;
  public int mcuPackets,graphicsPages,mutations,returns;public uint sum;
  public void Send(byte[] p){
   if(phase=="data"&&mcuPackets<4096){
    Require(p.Length==64,"Mock MCU packet length");if(fault=="mcu_transfer"&&mcuPackets==20)throw new IOException("Injected MCU transfer failure");
    for(int i=0;i<64;i+=2)sum+=(uint)(p[i]|p[i+1]<<8);mcuPackets++;return;
   }
   last=(byte[])p.Clone();
   if(p[0]==4&&p.Length==64&&p[1]!=0xaa){
    if(p[1]==0x18)phase="graphics_entry";
    else if(p[1]==0x38){Require((p[8]|p[9]<<8)==1807,"Mock SPI bound");phase="graphics";}
    else if(p[1]==2){Require(graphicsPages==1807,"Mock incomplete graphics apply");phase="apply";}
    else if(p[1]==0xf0)phase="done";
   }else if(p[0]==1)phase="identify";
   else if(p[0]==2){mutations++;phase="prepare";}
   else if(p[0]==3){Require(Hex(new byte[]{p[4],p[5],p[6],p[7]})=="ffff5a5a","Mock options changed");phase="options";}
   else if(p[0]==4){Require(p[4]==0&&p[5]==0&&p[8]==0&&p[9]==1,"Mock erase extent");phase="erase";}
   else if(p[0]==5){Require(p[8]==0&&p[9]==0x10,"Mock data extent");phase="data";}
   else if(p[0]==7){returns++;phase="returned";}
  }
  public byte[] Reply(){
   byte[] p=new byte[64];if(last!=null)Array.Copy(last,p,Math.Min(last.Length,64));
   if(phase.StartsWith("graphics")||phase=="apply"||phase=="done"){p[3]=1;if(fault=="graphics_apply"&&phase=="apply")p[3]=0xff;return p;}
   for(int i=4;i<8;i++)p[i]=0xfa;
   if(phase=="identify"){p[8]=(byte)(fault=="chip"?0x21:0x20);p[9]=5;p[10]=p[11]=0;p[12]=p[13]=0xff;p[14]=p[15]=0x5a;}
   else if(phase=="erase"){p[8]=0;p[9]=0;}
   else if(phase=="data"&&mcuPackets==4096){ushort checksum=(ushort)sum;if(fault=="checksum")checksum^=1;p[8]=(byte)checksum;p[9]=(byte)(checksum>>8);}
   return p;
  }
 }
 static void Require(bool b,string m){if(!b)throw new InvalidOperationException(m);}
 static void Notify(string phase){Current.phase=phase;if(Progress!=null)Progress(Current);}
 static byte[] Cmd(byte op){byte[] b=new byte[64];b[0]=op;b[1]=0xaa;b[2]=0x55;return b;}
 static byte[] GraphicsCmd(byte op){byte[] b=new byte[64];b[0]=4;b[1]=op;return b;}
 static void HashCheck(byte[] b,string hash){using(SHA256 s=SHA256.Create()){Require(Hex(s.ComputeHash(b))==hash,"Payload SHA256 mismatch");}}
 static ushort Sum16(byte[] b){uint sum=0;for(int i=0;i<b.Length;i+=2)sum+=(uint)(b[i]|b[i+1]<<8);return (ushort)sum;}
 static string PathFor(string instance){return @"\\?\"+instance.Replace("\\","#")+@"#{4d1e55b2-f16f-11cf-88cb-001111000030}";}
 static SafeFileHandle Open(string instance,ushort usage,bool overlapped,ushort revision) {
  if(mock!=null)return new SafeFileHandle(IntPtr.Zero,false);
  Require(instance.StartsWith("HID\\VID_0C45&PID_800A&",StringComparison.OrdinalIgnoreCase),"Unexpected HID instance");
  SafeFileHandle h=CreateFile(PathFor(instance),0xc0000000,3,IntPtr.Zero,3,overlapped?0x40000000u:0,IntPtr.Zero);
  try{
   Require(!h.IsInvalid,"HID open failed: "+Marshal.GetLastWin32Error());
   ATTR a=new ATTR();a.Size=Marshal.SizeOf(typeof(ATTR));
   Require(HidD_GetAttributes(h,ref a)&&a.VendorID==0x0c45&&a.ProductID==0x800a,"HID identity mismatch");
   if(revision!=0)Require(a.VersionNumber==revision,"HID revision mismatch");
   CAPS caps;IntPtr pp;Require(HidD_GetPreparsedData(h,out pp),"Missing HID preparsed data");
   try{Require(HidP_GetCaps(pp,out caps)>=0,"Invalid HID caps");}finally{HidD_FreePreparsedData(pp);}
   Require(caps.UsagePage==usage,"Unexpected HID usage");
   if(usage==0xff13)Require(caps.FeatureReportByteLength==65,"Expected 65-byte feature");
   if(usage==0xff68)Require(caps.OutputReportByteLength==4097&&caps.InputReportByteLength==65,"Expected 4097-out/65-in interrupt descriptor");
   return h;
  }catch{h.Dispose();throw;}
 }
 static void Set(SafeFileHandle h,byte[] payload) {
  Require(payload.Length<=64,"Oversized feature payload");
  if(mock!=null){mock.Send(payload);return;}
  byte[] report=new byte[65];Array.Copy(payload,0,report,1,payload.Length);
  Require(HidD_SetFeature(h,report,65),"SetFeature failed: "+Marshal.GetLastWin32Error());
 }
 static byte[] Get(SafeFileHandle h) {
  if(mock!=null)return mock.Reply();
  byte[] report=new byte[65];Require(HidD_GetFeature(h,report,65),"GetFeature failed: "+Marshal.GetLastWin32Error());
  Require(report[0]==0,"Unexpected feature report ID");byte[] p=new byte[64];Array.Copy(report,1,p,0,64);return p;
 }
 static void Header(byte[] b,byte op,bool ack) {
  Require(b.Length==64&&b[0]==op&&b[1]==0xaa&&b[2]==0x55&&b[3]==0,"MCU reply header mismatch");
  if(ack)Require(b[4]==0xfa&&b[5]==0xfa&&b[6]==0xfa&&b[7]==0xfa,"MCU operation rejected");
 }
 public static string ProbeGraphicsBegin(string command){using(SafeFileHandle h=Open(command,0xff13,false,0x0107)){return Hex(GraphicsExchange(h,0x18,35));}}
 public static string ReadLastGraphicsReply(string command){using(SafeFileHandle h=Open(command,0xff13,false,0x0107)){return Hex(Get(h));}}
 public static bool IsInterface(string instance,ushort usage,ushort revision){try{using(SafeFileHandle h=Open(instance,usage,usage==0xff68,revision)){}return true;}catch{return false;}}
 public static void Preflight(string command,string data,ushort revision) {
  using(SafeFileHandle h=Open(command,0xff13,false,revision)){}
  using(SafeFileHandle h=Open(data,0xff68,true,revision)){}
 }
 public static Evidence ProgramMcu(string command,byte[] fw) {
  HashCheck(fw,"4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b");
  Require(fw.Length==262144,"Expected 256KB MCU image");
  Current=new Evidence();Current.firmware_sha256="4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b";
  Current.expected_checksum=Sum16(fw);Require(Current.expected_checksum==0x2bef,"Unexpected MCU checksum");
  bool entry=false,verified=false;Exception failure=null;
  try {
   using(SafeFileHandle initial=Open(command,0xff13,false,0x0107)){}
   entry=true;Notify("mcu_entry");
   using(SafeFileHandle h=Open(command,0xff13,false,0)){Set(h,new byte[]{0xaa,0x42,0x89,0x5a,0xff,0x71,0x62,0xcc});Pause(30);Current.events.Add("HFD entry reply "+Hex(Get(h)));}
   Pause(500);
   using(SafeFileHandle h=Open(command,0xff13,false,0)){
    Set(h,Cmd(1));Pause(30);byte[] id=Get(h);Header(id,1,true);
    Current.chip_id=Hex(new byte[]{id[8],id[9],id[10],id[11]});
    Current.options=Hex(new byte[]{id[12],id[13],id[14],id[15]});
    Require(Current.chip_id=="20050000","Unexpected MCU chip ID");
    Require(Current.options=="ffff5a5a","MCU option bytes changed since identification");
    Current.events.Add("01 chip 20050000 options ffff5a5a");
    Notify("mcu_prepare");Current.mcu_mutation_started=true;
    Set(h,Cmd(2));Pause(30);
    byte[] opts=Cmd(3);Array.Copy(id,12,opts,4,4);Set(h,opts);Pause(30);
    Notify("mcu_erase");byte[] erase=Cmd(4);erase[9]=1;Set(h,erase);
    Pause(1000);byte[] erased=Get(h);Header(erased,4,true);
    Require(erased[8]==0&&erased[9]==0,"MCU erase returned an error");
    Current.events.Add("04 erase result 0000 verified");
    byte[] start=Cmd(5);start[9]=0x10;Set(h,start);Pause(30);Header(Get(h),5,true);
    Notify("mcu_program");
    byte[] packet=new byte[64];
    for(int i=0;i<4096;i++){
     Array.Copy(fw,i*64,packet,0,64);Set(h,packet);Current.mcu_packets=i+1;Current.mcu_bytes=(i+1)*64;
     Pause(2);
     if((i+1)%256==0)Notify("mcu_program");
    }
    Pause(200);byte[] final=Get(h);Header(final,5,true);
    Current.mcu_checksum=final[8]|final[9]<<8;
    Require(Current.mcu_checksum==Current.expected_checksum,"MCU final checksum mismatch");
    verified=true;Current.mcu_checksum_verified=true;Current.events.Add("05 checksum 2bef verified");
   }
  }catch(Exception ex){failure=ex;Current.error=ex.Message;}
  finally {
   // Do not launch an incompletely programmed application on transfer/checksum failure.
   if(entry&&(!Current.mcu_mutation_started||verified)){
    try{using(SafeFileHandle h=Open(command,0xff13,false,0)){Set(h,new byte[]{7,0xaa,0x55,0,0,0,0,0});Current.mcu_return_sent=true;}}
    catch(Exception ex){Current.error=(Current.error??"")+"; MCU return: "+ex.Message;if(failure==null)failure=ex;}
   }
   Notify(verified&&Current.mcu_return_sent?"mcu_complete":"mcu_failed");
  }
  if(failure!=null)throw new InvalidOperationException(Current.error,failure);
  return Current;
 }
 sealed class Io : IDisposable {
  SafeFileHandle handle;IntPtr ov,evt;GCHandle pin;bool pending,completed;
  public byte[] Buffer;
  public Io(SafeFileHandle h,byte[] b,bool write){
   handle=h;Buffer=b;
   if(mock!=null){if(write){Require(b.Length==4097,"Mock output geometry");if(mock.fault=="graphics_short")throw new IOException("Injected short write");mock.graphicsPages++;}return;}
   pin=GCHandle.Alloc(b,GCHandleType.Pinned);
   evt=CreateEvent(IntPtr.Zero,true,false,null);Require(evt!=IntPtr.Zero,"CreateEvent failed");
   ov=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(OVERLAPPED)));
   OVERLAPPED v=new OVERLAPPED();v.Event=evt;Marshal.StructureToPtr(v,ov,false);
   bool ok=write?WriteFile(h,pin.AddrOfPinnedObject(),(uint)b.Length,IntPtr.Zero,ov):ReadFile(h,pin.AddrOfPinnedObject(),(uint)b.Length,IntPtr.Zero,ov);
   int error=Marshal.GetLastWin32Error();pending=ok||error==997;
   if(!pending){Dispose();throw new InvalidOperationException("Interrupt I/O submission failed: "+error);}
  }
  public void Finish(uint timeout){
   if(mock!=null){if(Buffer.Length==65){Buffer[0]=0;Buffer[1]=1;Buffer[2]=0x5a;Buffer[3]=2;if(mock.fault=="graphics_ack")Buffer[3]=3;}return;}
   if(WaitForSingleObject(evt,timeout)!=0){CancelIoEx(handle,ov);uint ignored;GetOverlappedResult(handle,ov,out ignored,true);completed=true;throw new TimeoutException("Interrupt I/O timeout; cancelled and reaped");}
   uint n;bool ok=GetOverlappedResult(handle,ov,out n,false);completed=true;
   Require(ok&&n==(uint)Buffer.Length,"Interrupt I/O failed or short transfer");
  }
  public void Dispose(){
   if(ov!=IntPtr.Zero){if(pending&&!completed){CancelIoEx(handle,ov);uint ignored;GetOverlappedResult(handle,ov,out ignored,true);}Marshal.FreeHGlobal(ov);ov=IntPtr.Zero;}
   if(pin.IsAllocated)pin.Free();if(evt!=IntPtr.Zero){CloseHandle(evt);evt=IntPtr.Zero;}
  }
 }
 static byte[] GraphicsExchange(SafeFileHandle h,byte op,int wait){
  Set(h,GraphicsCmd(op));Pause(wait);byte[] p=Get(h);Pause(35);
  Current.events.Add("graphics "+op.ToString("X2")+" reply "+Hex(p));
  Require(p[0]==4&&p[1]==op&&p[3]==1,"Graphics command rejected: "+op.ToString("X2")+" reply "+Hex(p));return p;
 }
 static bool verifiedPriorMcuReceipt=false;
 public static void ReuseInstalledMcuReceipt(string firmwareHash,int checksum){
  Require(firmwareHash=="4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b"&&checksum==0x2bef,"Installed MCU receipt does not match");
  verifiedPriorMcuReceipt=true;
  Current=new Evidence();Current.firmware_sha256=firmwareHash;
  Current.events.Add("MCU unchanged; previous checksum receipt reused; MCU was not programmed in this run");
 }
 public static Evidence ProgramGraphics(string command,string data,byte[] spi){
  HashCheck(spi,"5cda49967d090aaeeaf564a47aa47890955ede7e9315165356c61361f7c92c0b");
  Require(spi.Length==7401472&&spi.Length%4096==0&&spi.Length<0x740000,"Invalid graphics bound");
  Require((Current.mcu_checksum_verified&&Current.mcu_return_sent)||verifiedPriorMcuReceipt,"Matching MCU installation receipt required");
  Current.graphics_sha256="5cda49967d090aaeeaf564a47aa47890955ede7e9315165356c61361f7c92c0b";
  try{
   using(SafeFileHandle cmd=Open(command,0xff13,false,0x0107))
   using(SafeFileHandle dat=Open(data,0xff68,true,0x0107)){
    Notify("graphics_entry");GraphicsExchange(cmd,0x18,35);Current.graphics_begin=true;
    byte[] addr=GraphicsCmd(0x38);int pages=spi.Length/4096;addr[8]=(byte)pages;addr[9]=(byte)(pages>>8);
    Set(cmd,addr);Pause(35);byte[] response=Get(cmd);Pause(35);
    Require(response[0]==4&&response[1]==0x38&&response[3]==1,"Graphics range setup rejected");
    Pause(500);Require(mock!=null||HidD_FlushQueue(dat),"Cannot flush old graphics ACKs");Notify("graphics_program");
    for(int page=0;page<pages;page++){
     byte[] payload=new byte[4097];Array.Copy(spi,page*4096,payload,1,4096);
     using(Io ack=new Io(dat,new byte[65],false)){
      using(Io write=new Io(dat,payload,true)){write.Finish(3000);}
      ack.Finish(5000);
      Require(ack.Buffer[0]==0&&ack.Buffer[1]==1&&ack.Buffer[2]==0x5a&&ack.Buffer[3]==2,"Invalid graphics page ACK");
     }
     Current.graphics_pages=page+1;Current.graphics_bytes=(page+1)*4096;
     if((page+1)%32==0||page+1==pages)Notify("graphics_program");
    }
    Notify("graphics_apply");GraphicsExchange(cmd,2,35);Current.graphics_apply_verified=true;
    Notify("graphics_finalize");GraphicsExchange(cmd,0xf0,35);Current.graphics_finalize_verified=true;
   }
   Notify("installation_transferred");return Current;
  }catch(Exception ex){Current.error=ex.Message;Notify("graphics_failed");throw;}
 }
 public static string[] SelfTest(byte[] fw,byte[] spi){
  InspectPayloads(fw,spi);List<string> results=new List<string>();
  Action<Evidence> saved=Progress;Progress=null;
  try{
   foreach(string fault in new string[]{"none","chip","checksum","mcu_transfer","graphics_ack","graphics_short","graphics_apply"}){
    mock=new MockState();mock.fault=fault;bool threw=false;
    try{ProgramMcu("mock",fw);ProgramGraphics("mock","mock",spi);}catch(Exception){threw=true;}
    Require(threw==(fault!="none"),"Self-test result: "+fault);
    if(fault=="none")Require(Current.mcu_checksum_verified&&Current.graphics_finalize_verified&&mock.graphicsPages==1807&&mock.mcuPackets==4096,"Self-test complete transfer");
    if(fault=="chip")Require(mock.mutations==0&&mock.returns==1,"Self-test chip failure must return before writes");
    if(fault=="checksum"||fault=="mcu_transfer")Require(mock.returns==0&&!Current.mcu_checksum_verified,"Self-test incomplete MCU must stay in updater");
    if(fault.StartsWith("graphics"))Require(!Current.graphics_finalize_verified,"Self-test failed graphics must not finalize");
    results.Add(fault+": pass");
   }
  }finally{mock=null;Progress=saved;Current=new Evidence();}
  return results.ToArray();
 }
 public static string InspectPayloads(byte[] fw,byte[] spi){
  HashCheck(fw,"4383291939280af6d30fc962cdf60cf64d531ae10dcd56c2a99ed7ba9dd4a62b");
  HashCheck(spi,"5cda49967d090aaeeaf564a47aa47890955ede7e9315165356c61361f7c92c0b");
  Require(fw.Length==262144&&Sum16(fw)==0x2bef&&spi.Length==7401472&&spi.Length<0x740000,"Payload geometry invalid");
  return "256KB MCU, checksum 2bef; 1807 graphics pages, end 70f000; hashes match";
 }
}
