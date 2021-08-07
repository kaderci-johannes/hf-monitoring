#!/usr/bin/python

from sys import argv
from time import time, localtime, sleep
from ROOT import TFile, TH1D, kBlack, kWhite
import registers
from ngFECSendCommand import send_commands

def makeup(H,T=None,X=None,Y=None):
  if T is None:
    T=["Title"]*len(H)
  if X is None:
    X=["Time (min)"]*len(H)
  if Y is None:
    Y=["Counts"]*len(H)
  for h,t,x,y in zip(H,T,X,Y):
    h.SetLineColor(kWhite)
    h.SetMarkerStyle(8)
    h.SetMarkerSize(.5)
    h.SetMarkerColor(kBlack)
    h.SetStats(0)
    h.SetTitle(t)
    h.GetXaxis().SetTitle(x)
    h.GetYaxis().SetTitle(y)
    h.GetYaxis().SetMaxDigits(3)
#   h.SetMinimum(-1)
    h.Write()

port = 63000		#64004
host = "hcalngccm01"	#"hcal904daq04"

if(argv[1]=='-M'):
  t=int(argv[2])
if(argv[1]=='-H'):
  t=60*int(argv[2])

crates = [1,2,3,4]
regs = ['vtrx_rssi_i_rr','2V5_voltage_f_rr','fec-sfp_rx_power_f']
hnames = ['rssi','power']

cmds = ["tget HF%s0%i-%s r" %(pm,crate,str(regs).replace(' ','').replace('\'','')) for pm in ['P','M'] for crate in crates]
print(cmds)

fName = '_'.join([str(d) for d in localtime()[:6]])+'.root'
f = TFile.Open(fName,"RECREATE")

histos = [[TH1D("HF%s0%i_%s" %(pm,crate,hname),"HF%s0%i %s" %(pm,crate,hname),t,-.5,t-.5) for hname in hnames] for pm in ['P','M'] for crate in crates]
print([h.GetName() for histo in histos for h in histo])

T=time()

for i in range(t):
  while((time()-T)%60>.5):
    sleep(.25)
  out = send_commands(port,host,cmds)
  print(localtime()[3:6])
  print("")
# for c in range(len(crates)):
#   rsdec[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c],16))
#   rsdec_d[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c],16)-rsdec[c].GetBinContent(1)+1)
#   rsdec_d[c].Fill(i,-1)
#   prbs[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c+1],16))
#   prbs_d[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c+1],16)-prbs[c].GetBinContent(1)+1)
#   prbs_d[c].Fill(i,-1)
#   fecccm[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c+2],16))
#   fecccm_d[c].Fill(i,int(out[0]['result'].split(' ')[len(regs)*c+2],16)-fecccm[c].GetBinContent(1)+1)
#   fecccm_d[c].Fill(i,-1)

# data = [int(o,16) if o[1] == 'x' else float(o) for o in out]

  data_str = [o.get('result').split('$') for o in out]
  print(data_str)
  for histo,d in zip(histos,data_str):
    if(d[0] == 'ERROR!!'):
      histo[0].Fill(i,-1)
      histo[1].Fill(i,-1)
      continue
    x = [int(s,16) if s[1] == 'x' else float(s) for s in d]
    histo[0].Fill(i,x[0])
    histo[1].Fill(i,x[1])

  for histo,hname in zip(histos,hnames):
    pass
    #h.Fill(i,data_h[])
  sleep(3)

TITLE=["HF%s0%i %s" %(pm,crate,hname) for pm in ['P','M'] for crate in crates for hname in hnames]
print(TITLE)
makeup([h for histo in histos for h in histo],TITLE)

f.Close()
