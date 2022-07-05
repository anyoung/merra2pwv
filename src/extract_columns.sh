#!/bin/bash
out=column_data.csv
echo "#site(gamsberg=0;hess=1),y,m,d,h,pwv(um),iwp(kg*m^-2),lwp(kg*m^-2),o3(DU)" > ${out}
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
		s="0"
	elif [ ${s} == "hess" ] ; then
		s="1"
	else
		s="-1"
	fi
	y=`echo ${bf} | egrep -o "[0-9]{4}y" | egrep -o "[0-9]+"`
	m=`echo ${bf} | egrep -o "[0-9]{2}m" | egrep -o "[0-9]+"`
	d=`echo ${bf} | egrep -o "[0-9]{2}d" | egrep -o "[0-9]+"`
	h=`echo ${bf} | egrep -o "[0-9]{2}h" | egrep -o "[0-9]+"`
	echo "${s},${y},${m},${d},${h},${pwv},${iwp},${lwp},${o3}" >> ${out}
	if [ ${mPrev} != ${m} ] ; then
		echo "Starting ${y}/${m} for ${s}"
	fi
	mPrev=${m}
done
