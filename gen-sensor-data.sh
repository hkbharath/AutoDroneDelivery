#!/bin/bash

if [ "$#" -eq 1 ]
then
    python gen_sig_battery.py  --input-file $1
    python gen_gpx.py --input-file $1

elif [ "$#" -eq 2 ]
then
    python gen_sig_battery.py  --input-file $1
    python gen_sig_battery.py  --input-file $2

    python gen_gpx.py --input-file $1
    python gen_gpx.py --input-file $2

    python gen_collision.py --t1 $1 --t2 $2    
fi