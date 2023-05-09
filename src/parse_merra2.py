from glob import glob
import numpy as np
import re as regex
from scipy.interpolate import interp2d, RegularGridInterpolator

def get_data(filename,sites=None):
	"""Wrapper for get_data1 and get_data2.
	
	This wrapper tries to identify the which format the file has and
	calls the corresponding get_data[12] method."""

	wrapped = None
	with open(filename) as fh:
		# header line identical for both formats
		l1 = fh.readline()
		# if the second line is longitudes, use data2
		l2 = fh.readline()
		if l2.find('lon') == 0:
			wrapped = get_data2
		else:
			wrapped = get_data1
	return wrapped(filename,sites=sites)

def get_data2(filename,sites=None):
	"""Extract data from MERRA-2 ASCII format ca. 2023"""
	fh = open(filename)
	lines = fh.readlines()

	def get_grid_vars(line):
		var_str = [x.strip() for x in line.split(',')[1:]]
		var_map = dict(zip(var_str,range(len(var_str))))
		var = np.array([float(l) for l in var_str])
		return var,var_map

	lon,lon_map = get_grid_vars(lines[1])
	lat,lat_map = get_grid_vars(lines[2])
	pres,pres_map = get_grid_vars(lines[3])
	minu,minu_map = get_grid_vars(lines[4])
	hour = minu/60.
	lon[abs(lon) < 0.00001] = 0
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
	for line in lines[6:]:
		for var,name in zip((H,O3,QI,QL,RH,T),("H","O3","QI","QL","RH","T")):
			if line.find(name) == 0:
				if line.find(name + '.lon') == 0: continue
				val_minu = regex.findall("time=[\-]?[0-9]+(?:\.[0-9]+)?",line)[0].split('=')[1]
				ii_time = minu_map[val_minu]
				val_pres = regex.findall("lev=[\-]?[0-9]+(?:\.[0-9]+)?",line)[0].split('=')[1]
				jj_pres = pres_map[val_pres]
				val_lat = regex.findall("lat=[\-]?[0-9]+(?:\.[0-9]+)?",line)[0].split('=')[1]
				kk_lat = lat_map[val_lat]
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
					func = RegularGridInterpolator((lat,lon),var[ihour,ipres,:,:])
					data[site][name][ihour,ipres] = func(np.array([[site_lat,site_lon]]))
	return data

def get_data1(filename,sites=None):
	"""Extract data from MERRA-2 ASCII format ca. 2019"""
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
			if line.find(name + '[') == 0:
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
					func = RegularGridInterpolator((lat,lon),var[ihour,ipres,:,:])
					data[site][name][ihour,ipres] = func(np.array([[site_lat,site_lon]]))
	return data

if __name__ == "__main__":
	sites = {"gamsberg": (16.22309385609976,-23.34357719776235,2347),
	  "hesslo": (16.500478178158065,-23.271726947477347,1800),
	  "hesshi":(16.530082,-23.241986,1900),
	}
	data = {}
	for yy in range(2009,2021):
		data[yy] = {}
		for mm in range(1,13):
			data[yy][mm] = {}
			filenames = glob("/media/sf_test/amt/references/weather/Paine/data/merra-2/*Np.%4d%02d*" % (yy,mm))
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
