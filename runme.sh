#!/bin/bash

VENV_NAME="environment"
SERVER_CONFIG="server_setup.json"
RECORD_PREFIX="record"
CODEBASE="integrated"
SIMULATION="simulation"

if [[ "$1" == "help" || "$1" == "-h" ]]
then
    echo "Usage:"
    echo "runme.sh server <server id>"
    echo "runme.sh drone <drone id> <server id>"
    echo "runme.sh drone_monitor"
    echo "runme.sh help"
    exit 0
fi

if [ ! -d $VENV_NAME ]
then
    python3 -m venv $VENV_NAME
    if [ $? == 0 ]
    then
        echo "venv created"
    fi
    
    source $VENV_NAME/bin/activate

    pip install dependencies/*.whl
    if [ $? == 0 ]
    then
        echo "Installed dependencies"
    fi
else
    source $VENV_NAME/bin/activate
fi

if [[ "$1" == "drone" ]]
then
    python $CODEBASE/drone.py --drone-id $2 --server-id $3 --server-config $SERVER_CONFIG --simulation-dir $SIMULATION
elif [[ "$1" == "server" ]]
then
    python $CODEBASE/base_loc.py --server-id $2 --server-config $SERVER_CONFIG --record-dir "${RECORD_PREFIX}_$2"
elif [[ "$1" == "drone_monitor" ]]
then
    python $CODEBASE/drone.py --drone-id 3 --server-id 3 --server-config $SERVER_CONFIG --simulation-dir $SIMULATION
fi
