#!/bin/bash

helpFunction() {
   echo ""
   echo "Usage: $0 -s AzureSubscription -g MyAzureResourceGroup -z private-zones.txt"
   echo -e "\t-s Azure Subscription where Resource Group is located"
   echo -e "\t-g Azure Resource Group where private zones will be created"
   echo -e "\t-z Private Zones list to be created on Resource Group (line by line)"
   exit 1 # Exit script after printing help
}

# 0. Check if all parameters are correct
while getopts "s:g:z:" opt
do
   case "$opt" in
      s ) SubscriptionArg="$OPTARG" ;;
      g ) RGoupArg="$OPTARG" ;;
      z ) PZonesFilesArg="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$SubscriptionArg" ] || [ -z "$RGoupArg" ] || [ -z "$PZonesFilesArg" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

# 1. Parse input private zone list & Create private zone from each zone on list
FileLines=$(wc -l < $PZonesFilesArg)
Counter=1
col=$(($(tput cols)-100))

while read PZoneLine; do
  echo -e "\e[1m$(date +'%T') [$Counter of $FileLines]\e[0m     Creating \e[4m$PZoneLine\e[24m on \e[4m$RGoupArg\e[24m Resource Group for \e[4m$SubscriptionArg\e[24m subscription"
  # Launch AZ CLI command to create zone
  $(az network private-dns zone create --subscription $SubscriptionArg -g $RGoupArg -n $PZoneLine --no-wait --tags "Created by"=- "Support Time Window"=- "Request Ticket"=- Description=- )
  
  (( Counter++ ))
done <$PZonesFilesArg
