from glob import glob
import numpy as np
import regex
from scipy.interpolate import interp2d

def get_data(filename,sites=None):
	#"dat/MERRA2_400.inst3_3d_asm_Np.20180406.nc4.txt"
	fh = open(filename)
	lines = fh.readlines()

	hour = np.array([float(m)/60. for m in lines[-1].split(', ')[1:]])
	lon = np.array([float(l) for l in lines[-2].split(', ')[1:]])
	lon[abs(lon) < 0.00001] = 0
	pres = np.array([float(l) for l in lines[-3].split(', ')[1:]])
	lat = np.array([float(l) for l in lines[-4].split(', ')[1:]])
	lat[abs(lat) < 0.00001] = 0

	Nhour = len(hour)
	Nlon = len(lon)
	Npres = len(pres)
	Nlat = len(lat)

	data = {"hour":hour,"lon":lon,"lat":lat,"pres":pres,"raw": {}}

	H = np.zeros((Nhour,Npres,Nlat,Nlon))
	O3 = np.zeros((Nhour,Npres,Nlat,Nlon))
	QI = np.zeros((Nhour,Npres,Nlat,Nlon))
	QL = np.zeros((Nhour,Npres,Nlat,Nlon))
	RH = np.zeros((Nhour,Npres,Nlat,Nlon))
	T = np.zeros((Nhour,Npres,Nlat,Nlon))
	for line in lines:
		for var,name in zip((H,O3,QI,QL,RH,T),("H","O3","QI","QL","RH","T")):
			if line.find(name) > -1:
				coords = regex.findall("\[[0-9]+\]",line.split(", ")[0])
				ii_time = int(coords[0][1:-1])
				jj_pres = int(coords[1][1:-1])
				kk_lat = int(coords[2][1:-1])
				vals = np.array([float(v) for v in line.split(", ")[1:]])
				vals[vals > 1e14] = np.nan
				var[ii_time, jj_pres, kk_lat, :] = vals
			data["raw"][name] = var

	if sites is None:
		return data

	for site,site_lon_lat_alt in sites.items():
		site_lon,site_lat,site_alt = site_lon_lat_alt
		data[site] = {}
		for var,name in zip((H,O3,QI,QL,RH,T),("H","O3","QI","QL","RH","T")):
			data[site][name] = np.zeros((Nhour,Npres))
			for ihour,_ in enumerate(hour):
				for ipres,_ in enumerate(pres):
					func = interp2d(lon,lat,var[ihour,ipres,:,:])
					data[site][name][ihour,ipres] = func(site_lon,site_lat)
	return data

if __name__ == "__main__":
	sites = {"gamsberg": (16.22309385609976,-23.34357719776235,2347),
	  "hess": (16.500478178158065,-23.271726947477347,1800)}
	data = {}
	for yy in range(2011,2021):
		data[yy] = {}
		for mm in range(1,13):
			data[yy][mm] = {}
			filenames = glob("data/merra-2/*Np.%4d%02d*" % (yy,mm))
			Nf = len(filenames)
			print("Found %d files for month %d/%02d" % (Nf,yy,mm))
			daily_data = get_data(filenames[0],sites=sites)
			if 'h' not in data.keys():
				data['h'] = daily_data['hour']
			if 'P' not in data.keys():
				data['P'] = daily_data['pres']
			for site in sites.keys():
				data[yy][mm][site] = {}
				for key,val in daily_data[site].items():
					data[yy][mm][site][key] = np.zeros((Nf,) + val.shape)
					data[yy][mm][site][key][0,:] = val
			for ii,ff in enumerate(filenames):
				if ii==0:
					continue
				daily_data = get_data(ff,sites=sites)
				for site in sites.keys():
					for key,val in daily_data[site].items():
						data[yy][mm][site][key][ii,:] = val

	save_dict = {}
	for k1,v1 in data.items(): 
		 if not isinstance(v1,dict): 
			 save_dict[k1] = v1
			 continue
		 for k2,v2 in v1.items(): 
			 for k3,v3 in v2.items(): 
				 for k4,v4 in v3.items(): 
					 save_dict["%s_%s_%4dy%02dm" % (k3,k4,k1,k2)] = v4
	np.savez('data/sites/daily.npz',**save_dict)
