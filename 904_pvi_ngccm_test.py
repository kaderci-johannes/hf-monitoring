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

port = 63700
host = "hcal904daq02"

if(len(argv)<3):
  print('\nUsage:\n\n./pvi_ngccm_test.py -M <duration in minutes> -IT <data taking interval in seconds>\n\nor\n\n./pvi_ngccm_test.py -H <duration in hours> -TI <data taking interval in seconds>\n')
  exit()

for i in range(1,len(argv)):
  if(argv[i]=='-M'):
    t=int(argv[i+1])
  elif(argv[i]=='-H'):
    t=60*int(argv[i+1])
  if(argv[i]=='-TI'):
    dt=int(argv[i+1])

if(argv.count('-TI')==0):
  dt=10

crates = [17,18]
regs = ['vtrx_rssi_i_rr','2V5_voltage_f_rr','2V5_current_f_rr','fec-sfp_rx_power_f','m-vtrx-Bias_Current_rr','fec-sfp_tx_power_f','fec-sfp_tx_biascurrent_f','fec-sfp_temperature_f']
hnames = ['RSSI','Voltage','Current','Power','VTRX Bias Current','SFP TX Power','SFP TX Bias Current','SFP Temperature']

DATA = []
histos = [[TH1D("HF%i_%s" %(crate,hname.lower().replace(' ','_')),"HF%i %s" %(crate,hname),60*t/dt,-dt/120.,t-dt/120.) for hname in hnames] for crate in crates]
htitles=["HF%i %s" %(crate,hname) for crate in crates for hname in hnames]
cmds = ["get HF%i-%s" %(crate,reg) for crate in crates for reg in regs]

len_regs=len(regs)
len_out=len(cmds)

fName = '_'.join([str(d) if d>9 else '0'+str(d) for d in localtime()[:6]])+'.root'
f = TFile.Open(fName,"RECREATE")

makeup(histos,htitles)

T=time()

try:
  for i in range(60*t/dt):
    while((time()-T)%dt>.1):
      sleep(.05)
    out = send_commands(port,host,cmds)
    print(localtime()[3:6])
    DATA.append([[o.get('result').split(' ')[0] for o in out[i:i+len_regs]] for i in range(0,len_out,len_regs)])
#   print(DATA)
#   sleep(.3)
  exit()

except (SystemExit, KeyboardInterrupt):
  for i,data in enumerate(DATA):
    for histo,d in zip(histos,data):
#     if(d[0] == 'ERROR!!'):
#       for h in histo:
#         h.Fill(dt*i/60.,-1)
#         print("Register readouts required for %s: %s, filling -1 to %s." %(h.GetName(),d,h.GetName()))
#       continue
      x = [int(s,16) if s[:2] == '0x' else -1 if s == 'ERROR!!' else float(s) for s in d]
      if(x[0]<0 or x[1]<0):
        histo[0].Fill(dt*i/60.,-1)
      else:
        histo[0].Fill(dt*i/60.,(x[1]-x[0]*2.5/1024.)/1000.)
      histo[1].Fill(dt*i/60.,x[1])
      histo[2].Fill(dt*i/60.,x[2])
      histo[3].Fill(dt*i/60.,x[3])
      histo[4].Fill(dt*i/60.,x[4])
      histo[5].Fill(dt*i/60.,x[5])
      histo[6].Fill(dt*i/60.,x[6])
      histo[7].Fill(dt*i/60.,x[7])

  for histo in histos:
    for h in histo:
      f.Delete("%s;1" %(h.GetName()))
      h.Write()

#  print("\n\nHistos and titles comparison:")
#  print(htitles)
#  print([h.GetName() for histo in histos for h in histo])

  f.Close()
