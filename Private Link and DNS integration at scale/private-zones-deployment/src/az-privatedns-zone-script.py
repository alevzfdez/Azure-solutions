
######################################################################################
# 0. Set-up environment
######################################################################################
import subprocess, argparse
from tqdm import tqdm
from yaspin import yaspin

######################################################################################
# 1. Functions & Classes definition
######################################################################################
def load_argparse():
  # Set arguments to be parsed
  parser = argparse.ArgumentParser(description='Azure private DNS zone creator script')
  parser.add_argument('--subscription', '-s', dest='subscription', required=True, 
                      help='Azure Subscription where Resource Group is located')
  parser.add_argument('--group', '-g', dest='rgroup', required=True,
                      help='Azure Resource Group where private zones will be created')
  parser.add_argument('--file_zones', '-fz', dest='zone_list', required=True,
                      help='Private Zones list to be created on Resource Group (line by line)')
  # Check & set args
  return parser.parse_args()

class az_private_zone_dns(object):
  def __init__(self, subscription, rgourp, pzone_list):
    # Init az_pzone_dns JSON
    self.az_pzone_dns = {
      'subscription': subscription,
      'rgroup': rgourp,
      'pzone_arr': self.make_pzone_arr(pzone_list)
    }
  def make_pzone_arr(self, pzone_list):
    # Init pzone array list
    pzone_arr=[]
    with open(pzone_list, 'r') as pzones:
      pzone_lines=pzones.readlines()
      for pzone_line in pzone_lines:
        pzone_arr.append(pzone_line.rstrip())
    return pzone_arr
  

# Main Work
if __name__ == '__main__':
  args = load_argparse()
  az_pzone_dns=az_private_zone_dns(args.subscription, args.rgroup, args.zone_list)
  pzone_out=[]
  for idx, zone in enumerate(tqdm(az_pzone_dns.az_pzone_dns['pzone_arr'])):
    az_cli_cmd = 'az network private-dns zone create ' + \
      '--subscription "' + str(az_pzone_dns.az_pzone_dns['subscription']) + '"' + \
      ' -g "' + str(az_pzone_dns.az_pzone_dns['rgroup']) + '"' + \
      ' -n "' + zone + '"' + \
      ' --no-wait' + \
      ' --tags "Created by"=- "Support Time Window"=- "Request Ticket"=- Description=- '

    pzone_out.append(subprocess.check_output(az_cli_cmd, shell=True))
    
  with yaspin(text="Private zones creation", color="cyan") as spinner:
      spinner.ok("✔ ")