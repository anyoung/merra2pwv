#!/bin/bash
out="data/am-reduced/tau_data.csv"
freq=(22 86 230 345)
tauHeader=`for fr in ${freq[@]} ; do echo tau${fr} ; done`
tauHeader=`echo ${tauHeader} | sed s/" "/","/g`
TbHeader=`for fr in ${freq[@]} ; do echo Tb${fr} ; done`
TbHeader=`echo ${TbHeader} | sed s/" "/","/g`
cat >${out} <<EOL
# Opacity and brightness temperature data
# Sites are:
#   0 = Gamsberg
#   1 = HESS (low)
#   2 = HESS (high)
# Opacity (tau) is in neper
# Brightness temperature (Tb) is in kelvin
# Opacity and brightness temperatures are calculated at the frequency indicated (in GHz) by numeric suffix
site,year,month,day,hour,${tauHeader},${TbHeader}
EOL
mPrev="-1"
for f in data/am/*.out ; do
	#f=data/am/gamsberg_2011y01m01d00h.out
	tau=
	Tb=
	for ii in ${!freq[*]} ; do
		n=`echo "${freq[${ii}]} + 1" | bc`
		tau[${ii}]=`sed -n ${n}p ${f} | awk {'print $2;'}`
		Tb[${ii}]=`sed -n ${n}p ${f} | awk {'print $3;'}`
	done
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
	tau=`echo ${tau[*]} | sed s/" "/","/g`
	Tb=`echo ${Tb[*]} | sed s/" "/","/g`
	echo "${sn},${y},${m},${d},${h},${tau},${Tb}" >> ${out}
	if [ ${mPrev} != ${m} ] ; then
		echo "Done ${y}/${m} for ${s}"
	fi
	mPrev=${m}
done
