import numpy as np
from scipy.interpolate import interp1d
from datetime import timedelta
from os import system
from sys import argv

def compile_preamble(fmin=0,fmax=100e9,df=100e6):
	return """# Atmospheric model based on MERRA-2 data
#
?
? Usage:   am <basename>.amc
?

f %d GHz  %d GHz  %d MHz
output f GHz tau neper Tb K
tol 1e-4

T0 2.7 K
""" % (fmin/1e9,fmax/1e9,df/1e6)

def compile_layers(P, T, H, O3=None, RH=None, QL=None, QI=None, dry_air=True, lineshape=None):
	"""Compile set of layers representing atmospheric model
	
	Input arguments:
	  P         -  pressure [mbar]
	  T         -  temperature [K]
	  H         -  height [m]
	  O3        -  ozone mass mixing ratio [kg/kg]
	  RH        -  relative humidity [1]
	  QL        -  liquid water mass mixing ratio [kg/kg]
	  QI        -  ice water mass mixing ratio [kg/kg]
	  dry_air   -  True/False, whether to add dry air column per layer
	  lineshape -  specify lineshape to use if needed
	"""
	if len(T) != len(P):
		raise ValueError("There should be exactly one temperature per pressure layer.")
	if len(H) != len(P):
		raise ValueError("There should be exactly one height per pressure layer.")
	if O3 is not None:
		if len(O3) != len(P):
			raise ValueError("There should be exactly one ozone mixing ratio per pressure layer.")
	if RH is not None:
		if len(RH) != len(P):
			raise ValueError("There should be exactly one relative humidity per pressure layer.")
	if QL is not None:
		if len(QL) != len(P):
			raise ValueError("There should be exactly one liquid water content per pressure layer.")
	if QI is not None:
		if len(QI) != len(P):
			raise ValueError("There should be exactly one ice water content per pressure layer.")

	layers_str = """layer   # empty layer for top of atmosphere
Pbase 0 mbar
Tbase 217 K

"""

	prev_o3 = None
	prev_rh = None
	prev_qi = None
	prev_ql = None
	prev_h = None
	for ii in range(len(P)-1,-1,-1):
		p = P[ii]
		t = T[ii]
		h = H[ii]
		if np.isnan(t):
			continue
		if O3 is not None:
			if prev_o3 is not None:
				o3 = mmr_to_vmr((O3[ii] + prev_o3)/2,molecule="O3")
			else:
				o3 = mmr_to_vmr(O3[ii],molecule="O3")
			prev_o3 = O3[ii]
		else:
			o3 = None
		if RH is not None:
			if prev_rh is not None:
				rh = (RH[ii] + prev_rh)/2
			else:
				rh = RH[ii]
			prev_rh = RH[ii]
		else:
			rh = None
		if QI is not None:
			if prev_qi is not None and prev_h is not None:
				qi = mmr_to_density((QI[ii] + prev_qi)/2,(p+prev_t)/2,(t+prev_t/2)) * (prev_h-h)
				# cannot have qi at above ~ 273K
				if qi > 0 and t > 273:
					qi = None
			else:
				qi = None
			prev_qi = QI[ii]
		else:
			qi = None
		if QL is not None:
			if prev_ql is not None and prev_h is not None:
				ql = mmr_to_density((QL[ii] + prev_ql)/2,(p+prev_t)/2,(t+prev_t/2)) * (prev_h-h)
				# cannot have ql at below ~ 242K
				if ql > 0 and t < 242:
					ql = None
			else:
				ql = None
			prev_ql = QL[ii]
		else:
			ql = None
		prev_h = H[ii]
		prev_p = P[ii]
		prev_t = T[ii]

		layers_str += compile_layer(p,t,o3=o3,rh=rh,qi=qi,ql=ql,dry_air=dry_air,lineshape=lineshape)
		layers_str += "\n"

	return layers_str

def compile_layer(p, t, o3=None, rh=None, qi=None, ql=None, dry_air=True, lineshape=None, name=None):
	if name is None:
		if p < 1.0:
			name = "mesosphere"
		if p < 100.0:
			name = "stratosphere"
		else:
			name = "troposphere"
	layer_str = "layer {0}\n".format(name)
	layer_str += "Pbase {0:.3f} mbar\n".format(p)
	layer_str += "Tbase {0:.3f} K\n".format(t)
	if lineshape is not None:
		layer_str += "lineshape {0}\n".format(lineshape)
	if dry_air:
		layer_str += "column dry_air vmr\n"
	if o3 is not None:
		layer_str += "column o3 vmr {0}\n".format(o3)
	if rh is not None:
		layer_str += "column h2o RH {0:.3f}%\n".format(rh*100)
	if qi is not None and qi > 1e-10:
		layer_str += "column iwp_abs_Rayleigh {0} kg*m^-2\n".format(qi)
	if ql is not None and ql > 1e-10:
		layer_str += "column lwp_abs_Rayleigh {0} kg*m^-2\n".format(ql)

	return layer_str

def mmr_to_vmr(mmr,molecule=None,molar_mass=None):
	if molecule is None and molar_mass is None:
		raise ValueError("Either molecule or molar_mass need to be specified for mmr to vmr conversion")
	mm_dry_air = 28.9644
	if molecule == "O3":
		molar_mass = 47.9982
	return mmr * mm_dry_air / molar_mass

def air_density(P,T):
	"""Compute air density
	
	Input arguments:
	  P  -  pressure [mbar]
	  T  -  temperature [K]
	"""
	R_specific_dry_air = 287.058 # J/(kg*K)
	return 100*P/(R_specific_dry_air*T) # factor 100 to convert P from mbar to Pa

def mmr_to_density(mmr,P,T):
	return mmr * air_density(P,T)

def limit_height(H, H_min, *args):
	# remove nans
	idx = np.bitwise_not(np.isnan(H))
	H = H[idx]
	args = [a[idx] for a in args]
	# if lowest point above minimum height, return as-is
	if H[0] > H_min:
		return [H,] + args
	# interpolate to get exact minimum point
	b = [np.concatenate(((H_min,),H[H > H_min]))]
	for a in args:
		func = interp1d(H,a)
		b.append(np.concatenate(((func(H_min),),a[H > H_min])))
	return b

def average_by_month(x, days):
	shape = list(x.shape)
	shape[0] = 12
	X = np.zeros(shape)
	for ii,month in enumerate(range(1,13)):
		X[ii,:] = x[[d.month == month for d in days],:].mean(axis=0)

	return X

def median_by_month(x, days):
	shape = list(x.shape)
	shape[0] = 12
	X = np.zeros(shape)
	for ii,month in enumerate(range(1,13)):
		X[ii,:] = np.median(x[[d.month == month for d in days],:],axis=0)

	return X

def minimum_by_month(x, days):
	shape = list(x.shape)
	shape[0] = 12
	X = np.zeros(shape)
	for ii,month in enumerate(range(1,13)):
		X[ii,:] = x[[d.month == month for d in days],:].min(axis=0)

	return X

import signal, os
STOP = False

def handler(signum, frame):
	global STOP
	print('Signal handler called with signal', signum)
	STOP = True

# Set the signal handler
signal.signal(signal.SIGINT, handler)

if __name__ == "__main__":
	sites = {"gamsberg": (16.22309385609976,-23.34357719776235,2347),
	  "hesslo": (16.500478178158065,-23.271726947477347,1800),
	  "hesshi":(16.530082,-23.241986,1900),
	}
	fmt_str = "%s_{}_%4dy%02dm"
	din = np.load("data/sites/daily.npz")
	P = din["P"]
	h = din["h"]
	for yy in range(2009,2021):
		for mm in range(1,13):
			print("Year/Month: %4d/%02d" % (yy,mm))
			for site in sites.keys():
				print("    Site: %s" % site)
				fmt_str_par = fmt_str % (site,yy,mm)
				H = din[fmt_str_par.format("H")]
				O3 = din[fmt_str_par.format("O3")]
				QI = din[fmt_str_par.format("QI")]
				QL = din[fmt_str_par.format("QL")]
				RH = din[fmt_str_par.format("RH")]
				T = din[fmt_str_par.format("T")]
				for jj in range(H.shape[0]):
					dd = jj + 1
					for ii,hh in enumerate(h):
						base = "data/am/%s_%4dy%02dm%02dd%02dh" % (site,yy,mm,dd,hh)
						H_,P_,T_,O3_,RH_,QL_,QI_ = limit_height(H[jj,ii,:],sites[site][2],P,T[jj,ii,:],O3[jj,ii,:],RH[jj,ii,:],QL[jj,ii,:],QI[jj,ii,:])
						txt = compile_preamble(0e9,400e9,1e9) + compile_layers(P_,T_,H_,O3_,RH_,QL_,QI_)
						with open(base + ".amc","w") as fh:
							fh.write(txt)
						system("am {base}.amc 1>{base}.out 2>{base}.err".format(base=base))
						if STOP:
							exit(0)
