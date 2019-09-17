#!/usr/bin/env bash

# convience bash script that downloads the data and unzips the files, tested on linux

# making the raw data directory if does not exist
mkdir -p ./raw_data

# getting the published zip file - change this location if the remote changes
wget -O ./raw_data/all_raw.zip https://clinicaltrials.gov/AllPublicXML.zip

# unzips the raw file
unzip ./raw_data/all_raw.zip -d ./raw_data/

# clean up
rm ./raw_data/all_raw.zip