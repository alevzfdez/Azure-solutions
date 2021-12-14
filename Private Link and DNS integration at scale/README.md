# README

## Private Link and DNS integration at scale

This repo use python scripts in order to deploy "Private Link and DNS integration at scale" solution provided by [Microsoft](https://docs.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/private-link-and-dns-integration-at-scale).

This article describes how to integrate Azure Private Link for PaaS services with Azure Private DNS zones in hub and spoke network architectures.

Scripts used by this repo has 2 main tasks:
1.  Deploy all required private zones from input file at scale.
2. Deploy all required policies in order to deny public access and deploy if not exist resource DNS entry on private endpoints.


## Requirements ##

#### Requirements setup ###

For automatic setup, just allow run **setup** script. Choose between linux (Shell script) or Windows (PowerShell).
       
- Shell Script:
       
       chmod +x setup-linux.sh
       ./setup-linux.sh

- PowerShell (open as administrator):
       
       ./setup-win.ps1

## Script usage ##

Ensure you have your virtual environment activated and run required python script
       
- Linux:

       ./venv/bin/activate
       python3 private-zones-deployment/src/az-privatedns-zone-script.py -h
       python3 policies-deployment/src/az-privatedns-policy-script.py -h

- PowerShell:

       ./venv/Scripts/activate
       python private-zones-deployment/src/az-privatedns-zone-script.py -h
       python policies-deployment/src/az-privatedns-policy-script.py -h



Recommended documentation:
- [What is Azure Private Endpoint?](https://docs.microsoft.com/en-us/azure/private-link/private-endpoint-overview)
- [Azure Private Endpoint DNS configuration](https://docs.microsoft.com/en-us/azure/private-link/private-endpoint-dns)
- [Private Link and DNS integration at scale](https://docs.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/private-link-and-dns-integration-at-scale)




## LICENSE
### GNU GPL v3
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)