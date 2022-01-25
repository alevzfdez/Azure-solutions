

######################################################################################
# 0. Set-up environment
######################################################################################
import os, subprocess, coloredlogs, logging, argparse, json
from tqdm import tqdm
from yaspin import yaspin

######################################################################################
# 1. Functions definition
######################################################################################
def load_argparse():
  # Set arguments to be parsed
  parser = argparse.ArgumentParser(description='Azure private DNS policies creator script v1.0')

  parser.add_argument('--debug', '-d', dest='debug', choices=['on', 'off'], default='off',
                    help='Turn debugging mode on-off')
  parser.add_argument('--remove', '-r', dest='remove', default='no', choices=['no', 'yes'],
                      help='Rollback policies on list (remove them if set flag to 1).')
  parser.add_argument('--management-group', '-mg', dest='mgroup', required=True,
                      help='Azure Management Group where policy definition will be apply.')
  parser.add_argument('--file_zones', '-fz', dest='zone_list', required=True,
                      help='File with all required zones following template on folder.')

  # Check & set args
  return parser.parse_args()

# Debug Set
def str_to_bool(s):
    if s == 'on':
         return False
    elif s == 'off':
         return True
    else:
         raise ValueError
    return

# Set debug environment
def logging_set(args):
    handler = logging.StreamHandler()
    handler.addFilter(coloredlogs.HostNameFilter())
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    logger=logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.disabled=str_to_bool(args.debug)
    logging.debug(args)
    coloredlogs.install(level='DEBUG', logger=logger)
    return

# 1. Create or Remove definition
def az_pdefinition(args, pzone):
  if 'src' in os.listdir():
    templates_dir = 'src/templates/'
  else:
    templates_dir = 'templates/'

  # Gather existing templates on folder
  templates = os.listdir(templates_dir)
  policy_def_out = []

  for i in range(len(templates)):
    for idx, priv_zone in enumerate(pzone['private_zone']):
      # Set parameters from template definition
      with open(templates_dir+templates[i], 'r') as ffile:
        ffile = ffile.read()
        ffile = ffile.replace('{{subresource}}', pzone['subresource'])
        # Set as mucho providers as listed on input zone list before replacement on template
        cond_provider_1=[]
        cond_provider_2=[]
        for rprov in pzone['resource_provider']:
          cond_provider_1.append({
                "field": "type",
                "equals": rprov[:rprov.rfind('/')]
              })
          cond_provider_2.append({
                "field": rprov,
                "notEquals": pzone["condition"]
              })
        ffile = ffile.replace('{{resource_provider_1}}', json.dumps(cond_provider_1))
        ffile = ffile.replace('{{resource_provider_2}}', json.dumps(cond_provider_2))
        if idx > 0 and not '{{private_zone}}' in ffile:
          break
        else:
          ffile = ffile.replace('{{private_zone}}', str(priv_zone))

        templ = json.loads(ffile.replace('', ''))

      policy_def = {
        'name': templates[i].rstrip('.json')+'-'+pzone['resource_provider'][0].split('/')[0].split('.')[1]+'-'+pzone['subresource']+'-'+str(f"{idx+1:02d}"),
        'mode': templ['mode'],
        'mgroup': args.mgroup,
        'metadata': 'category=DNS',
        'rules': templ['policyRule'],
        'params': templ.get('parameters', '{}')
      }

      # Set AZ-CLI command & run
      if args.remove == 'no':
        az_cli_cmd = 'az policy definition create --name "' + str(policy_def.get('name')) + \
          '" --mode "' + str(policy_def['mode']) + \
          '" --metadata "' + str(policy_def['metadata']) + \
          '" --management-group "' + str(args.mgroup) + \
          '" --rules "' + str(policy_def['rules']).replace('"', '\\"') + \
          '" --params "' + str(policy_def['params']).replace('"', '\\"') + '"'

        az_cli_cmd = az_cli_cmd.replace('$', "\$")
        logging.debug(az_cli_cmd)
        policy_def_out.append(json.loads(subprocess.check_output(az_cli_cmd, shell=True)))
      else:
        az_cli_cmd = 'az policy definition delete --name "' + str(policy_def.get('name')) + \
          '" --management-group "' + str(args.mgroup) + '"'

        logging.debug(az_cli_cmd)
        policy_def_out.append(subprocess.check_output(az_cli_cmd, shell=True))

  return policy_def, policy_def_out

# 2. Create initiative & bind definitions
def az_pinitiative(args, policy_def_out, set_name):

  set_list=[]

  # Set AZ-CLI command & run
  if args.remove == 'no':
    for i in range(len(policy_def_out)):
      for j in range(len(policy_def_out[i]['policy_def_out'])):
        set_list.append({'policyDefinitionId': policy_def_out[i]['policy_def_out'][j]['id']})

    logging.debug(json.dumps(set_list, indent=2))

    az_cli_cmd = 'az policy set-definition create' + \
      ' --management-group "' + str(args.mgroup) + '"' + \
      ' --metadata "' + 'category=DNS' + '"' + \
      ' --name "' + set_name + '"' + \
      ' --definitions "' + str(set_list) + '"'

    logging.debug(az_cli_cmd)
    policy_init_out = json.loads(subprocess.check_output(az_cli_cmd, shell=True))
  else:
    az_cli_cmd = 'az policy set-definition delete' + \
      ' --management-group "' + str(args.mgroup) + '"' + \
      ' --name "' + set_name + '"'

    logging.debug(az_cli_cmd)
    policy_init_out = subprocess.check_output(az_cli_cmd, shell=True)


  return policy_init_out

# 3. Make assignment to input MGroup
def az_pinitassignment(args, set_name):
  location_mg='westeurope'

  # Get MGroup ID name
  az_cli_cmd = 'az account management-group show ' + \
    '--name "' + str(args.mgroup) + '"'

  logging.debug(json.dumps(az_cli_cmd, indent=2))
  mgroup_out = json.loads(subprocess.check_output(az_cli_cmd, shell=True))

  # Get Initiative ID from name
  az_cli_cmd = 'az policy set-definition list ' + \
    ' --management-group "' + str(args.mgroup) + '"' + \
    ' --query "[? id!=\'null\']|[? contains(id, \'' + set_name + '\')].id"'

  logging.debug(az_cli_cmd)
  initiative_out = json.loads(subprocess.check_output(az_cli_cmd, shell=True))[0]

  # Set AZ-CLI command & run
  if args.remove == 'no':
    az_cli_cmd = 'az policy assignment create' + \
      ' --scope "' + mgroup_out['id'] + '"' + \
      ' --name "' + set_name + '"' + \
      ' --policy-set-definition "' + initiative_out + '"' + \
      ' --assign-identity'+ \
      ' --location "' + location_mg + '"'

    logging.debug(az_cli_cmd)
    policy_init_assign_out = json.loads(subprocess.check_output(az_cli_cmd, shell=True))
  else:
    print("Please, ensure Policy assignment has been manualy removed.")
    input("Press Enter to continue...")

    logging.debug(az_cli_cmd)
    policy_init_assign_out = subprocess.check_output(az_cli_cmd, shell=True)
    pass


  return policy_init_assign_out


# Main Work
if __name__ == '__main__':
  args = load_argparse()
  logging_set(args)
  spinner = yaspin(color="yellow")
  print('\n')

  pzone_arr = json.load(open(args.zone_list, 'r'))

  # 1. Policy definitions
  policy_def_out = []
  policy_def_set = []
  set_name='Private DNS Initiative'

  if args.remove == 'no':
    
    
    for idx, pzone in enumerate(tqdm(pzone_arr, desc='Policy definitions creation')):
      try:
        policy_def_set_unit, policy_def_out_unit = az_pdefinition(args, pzone)
        policy_def_set.append({'policy_def_set': policy_def_set_unit})
        policy_def_out.append({'policy_def_out': policy_def_out_unit})

      except:
        print ("Something went wrong, program has aborted.")
        exit()
    with yaspin(text="Policy definitions creation", color="cyan") as spinner:
      spinner.ok("✔ ")

    # 2. Policy initiative
    with yaspin(text="Policy initiative creation", color="cyan") as spinner:
      policy_init_out = az_pinitiative(args, policy_def_out, set_name)
      spinner.ok("✔ ")
    
    #print ('✔\tPolicy Initiative creation')

    # 3. Assign initiative
    with yaspin(text="Policy assignment creation", color="cyan") as spinner:
      policy_init_assign_out = az_pinitassignment(args, set_name)
      spinner.ok("✔ ")
    
    #print ('✔\tPolicy Assignment creation')

  else:
    # 1. Remove initiative assignment
    policy_init_assign_out = az_pinitassignment(args, set_name)
    #print ('\nConfirm assignment has been deleted.')

    # 2. Remove policy initiative
    with yaspin(text="Policy initiative deletion", color="magenta") as spinner:
      policy_init_out = az_pinitiative(args, {}, set_name)
      spinner.ok("✔ ")

    # 3. Remove Policy definitions
    
    for idx, pzone in enumerate(tqdm(pzone_arr, desc='Policy definitions deletion')):
      try:
        az_pdefinition(args, pzone)
      except:
        print ("Something went wrong, execution aborted.")
        exit()
    with yaspin(text="Policy definitions deletion", color="magenta") as spinner:
      spinner.ok("✔ ")

  print (" ------------------------------- ")
  print (" -- All done! Please check it -- ")

