#!/bin/bash

strategy="run_debug"
model=$1
dataset=$2

cd ..
python -m programming.main \
  --strategy $strategy \
  --model $model \
  --dataset $dataset
