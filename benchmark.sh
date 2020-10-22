#!/bin/bash

echo "debut du test"

server_address='134.214.202.240'
filename='benchmark.bin'
benchmark='benchmark.csv'
filesize=5000
echo "$server_address"

dd if=/dev/urandom of=$filename bs=1k count=$filesize

echo "WINDOW_SIZE;TIMER;MAX_ACK_RETRANSMIT;filesize;time" >> $benchmark

for WINDOW_SIZE in '2' '4' '6' '8' '10' '12' '14' '16' '32';
do
    for TIMER in '0.0001' '0.0002' '0.0005' '0.001' '0.002' '0.005' '0.01' '0.02' '0.05'
    do
        for MAX_ACK_RETRANSMIT in '1' '2' '3' '4'
        do
            echo "WINDOW_LENGTH : $WINDOW_SIZE"
            echo "TIMER : $TIMER"
            echo "MAX_ACK_RETRANSMIT: $MAX_ACK_RETRANSMIT"
            echo "FILESIZE: $filesize"

            python3 server.py 3000 --one-shot 1 --timer $TIMER --window-size $WINDOW_SIZE --max-duplicate-ack $MAX_ACK_RETRANSMIT > server.log 2>&1 &
            time=$( (time ./client1 $server_address 3000 $filename 0) 2>&1 | perl -nle 'print $1 if /real\s+\d+m([,\d]+)s/' | tr ',' '.')

            echo "time: $time"

            echo "$WINDOW_SIZE;$TIMER;$MAX_ACK_RETRANSMIT;$filesize;$time" >> $benchmark
            
            sleep 1
            echo
            echo
            echo
        done
    done
done
