#!/bin/bash
out=tau_data.csv
freq=(22 90 230 345)
tauHeader=`for fr in ${freq[@]} ; do echo tau${fr} ; done`
tauHeader=`echo ${tauHeader} | sed s/" "/","/g`
echo "#site(gamsberg=0;hess=1),y,m,d,h,${tauHeader}" > ${out}
mPrev="-1"
for f in data/am/*.out ; do
	#f=data/am/gamsberg_2011y01m01d00h.out
	tau=
	for ii in ${!freq[*]} ; do
		n=`echo "${freq[${ii}]} + 1" | bc`
		tau[${ii}]=`sed -n ${n}p ${f} | awk {'print $2;'}`
	done
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
	tau=`echo ${tau[*]} | sed s/" "/","/g`
	echo "${s},${y},${m},${d},${h},${tau}" >> ${out}
	if [ ${mPrev} != ${m} ] ; then
		echo "Starting ${y}/${m} for ${s}"
	fi
	mPrev=${m}
done
