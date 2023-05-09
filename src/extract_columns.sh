#!/bin/bash
out="data/am-reduced/column_data.csv"
cat >${out} <<EOL
# Water column data
# Sites are:
#   0 = Gamsberg
#   1 = HESS (low)
#   2 = HESS (high)
# Precipitable water vapour (pwv) is in micron
# Ice water (iwp) is in kg/m^2
# Liquid water (lwp) is in kg/m^2
# Ozone (o3) is in Dobson units
# Opacity and brightness temperatures are calculated at the frequency indicated (in GHz) by numeric suffix
site,year,month,day,hour,pwv,iwp,lwp,o3
EOL
mPrev="-1"
for f in data/am/*.err ; do
	#f=data/am/gamsberg_2011y04m27d15h.err
	total=`grep -A99 total ${f}`
	pwv=`echo "$total" | grep -A1 h2o | grep um_pwv | awk '{print $2;}' | egrep -o "[0-9\.e\+\-]+"`
	if [ -z ${pwv} ] ; then
		pwv="0"
	fi
	iwp=`echo "$total" | grep -A1 iwp | grep "kg" | awk '{print $2;}' | egrep -o "[0-9\.e\+\-]+"`
	if [ -z ${iwp} ] ; then
		iwp="0"
	fi
	lwp=`echo "$total" | grep -A1 lwp | grep "kg" | awk '{print $2;}' | egrep -o "[0-9\.e\+\-]+"`
	if [ -z ${lwp} ] ; then
		lwp="0"
	fi
	o3=`echo "$total" | grep -A1 o3 | grep "DU" | awk '{print $2;}' | egrep -o "[0-9\.e\+\-]+"`
	if [ -z ${o3} ] ; then
		o3="0"
	fi
	bf=`basename -s .err $f`
	s=`echo $bf | egrep -o "^[^_]+"`
	if [ ${s} == "gamsberg" ] ; then
		sn="0"
	elif [ ${s} == "hesslo" ] ; then
		sn="1"
	elif [ ${s} == "hesshi" ] ; then
		sn="2"
	else
		sn="-1"
	fi
	y=`echo ${bf} | egrep -o "[0-9]{4}y" | egrep -o "[0-9]+"`
	m=`echo ${bf} | egrep -o "[0-9]{2}m" | egrep -o "[0-9]+"`
	d=`echo ${bf} | egrep -o "[0-9]{2}d" | egrep -o "[0-9]+"`
	h=`echo ${bf} | egrep -o "[0-9]{2}h" | egrep -o "[0-9]+"`
	echo "${sn},${y},${m},${d},${h},${pwv},${iwp},${lwp},${o3}" >> ${out}
	if [ ${mPrev} != ${m} ] ; then
		echo "Done ${y}/${m} for ${s}"
	fi
	mPrev=${m}
done
