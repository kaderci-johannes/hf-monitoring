#!/usr/bin/python 

from sys import argv
from time import time, localtime, sleep
from ROOT import TFile, TH1D, kBlack, kWhite
from ngFECSendCommand import send_commands
#import registers

def makeup(H,T=None,X=None,Y=None):
  if(type(H[0]) is list):
    HH=[h for histo in H for h in histo]
  else:
    HH=H
  if T is None:
    T=["Title"]*len(HH)
  if X is None:
    X=["Time (min)"]*len(HH)
  if Y is None:
    Y=["Value"]*len(HH)
  for h,t,x,y in zip(HH,T,X,Y):
    h.SetLineColor(kWhite)
    h.SetMarkerStyle(8)
    h.SetMarkerSize(.5)
    h.SetMarkerColor(kBlack)
    h.SetStats(0)
    h.SetTitle(t)
    h.GetXaxis().SetTitle(x)
    h.GetYaxis().SetTitle(y)
    h.GetYaxis().SetMaxDigits(3)
    h.Write()

port = 63000
host = "hcalngccm01"

if(argv[1]=='-M'):
  t=int(argv[2])
if(argv[1]=='-H'):
  t=60*int(argv[2])

crates = [1,2,3,4]
regs = ['vtrx_rssi_i_rr','2V5_voltage_f_rr','2V5_current_f_rr','fec-sfp_rx_power_f']
hnames = ['RSSI','Voltage','Current','Power']

histos = [[TH1D("HF%s0%i_%s" %(pm,crate,hname.lower()),"HF%s0%i %s" %(pm,crate,hname),t,-.5,t-.5) for hname in hnames] for pm in ['P','M'] for crate in crates]
htitles=["HF%s0%i %s" %(pm,crate,hname) for pm in ['P','M'] for crate in crates for hname in hnames]
cmds = ["tget HF%s0%i-%s r" %(pm,crate,str(regs).replace(' ','').replace('\'','')) for pm in ['P','M'] for crate in crates]
#print(cmds)
#print('')
#print([h.GetName() for histo in histos for h in histo])

fName = '_'.join([str(d) if d>9 else '0'+str(d) for d in localtime()[:6]])+'.root'
f = TFile.Open(fName,"RECREATE")

makeup(histos,htitles)

T=time()

for i in range(t):
  while((time()-T)%60>.5):
    sleep(.25)
  out = send_commands(port,host,cmds)
  print(localtime()[3:6])
  data_str = [o.get('result').split('$') for o in out]

# print('')
# print([(o.get('cmd'),o.get('result').split('$')) for o in out])

  for histo,d in zip(histos,data_str):
    if(d[0] == 'ERROR!!'):
      for h in histo:
        h.Fill(i,-1)
        f.Delete("%s;1" %(h.GetName()))
        h.Write()
        print("Register readouts required for %s: %s, filling -1 to %s." %(h.GetName(),d,h.GetName()))
      continue
    x = [int(s,16) if s[1] == 'x' else float(s) for s in d]
#   print(x)
    histo[0].Fill(i,(x[1]-x[0]*2.5/1024.)/1000.)
    histo[1].Fill(i,x[1])
    histo[2].Fill(i,x[2])
    histo[3].Fill(i,x[3])
    for h in histo:
      f.Delete("%s;1" %(h.GetName()))
      h.Write()
  sleep(3)

#print("\n\nHistos and titles comparison:")
#print(htitles)
#print([h.GetName() for histo in histos for h in histo])

f.Close()
