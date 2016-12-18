#!/bin/bash

sudo sshfs -C -o StrictHostKeyChecking=no,Ciphers=arcfour,IdentityFile=$3,allow_other,defer_permissions,port=$2 $1@localhost:/scratch/olympus /mnt/olympus
