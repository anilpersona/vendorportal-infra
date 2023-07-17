#!/bin/bash

if [[ $(git diff HEAD^ HEAD "$1") ]]; then
  printf "1"
else
  printf "0"
fi