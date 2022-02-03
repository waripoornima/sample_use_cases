"""
    This is part of Spirent Communication Green initiative project
    This will help to save the power by turning on the power only when reservation starts

    Author : Poornima Wari
    Date   : 20 oct 2021

"""


# trace error
def error_handling():
    """
        This definition is to trace the Error
        :return: format to trace the exception
    """
    return 'Error: {}.{},line:{}'.format(sys.exc_info()[0], sys.exc_info()[1],
                                             sys.exc_info()[2].tb_lineno)


import paramiko                                                                 # we need it for ssh
import logging                                                                  # we need it for loggers
import platform                                                                 # we need it for python version
import os                                                                       # we need to for environment variables
import sys                                                                      # we need this to load lib path
from time import sleep                                                          # we need it for pause
from urllib.parse import urlsplit                                               # we need this to split the url
from py_velocity_rest_client.Velocity import Velocity                           # we need it for Velocity ReST request
from py_velocity_topology_parser.VelocityTopologyParser import VelocityTopologyParser # we need it tp parse the topology


# set the logger format for velocity
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# get the topology reservation id and velocity url
try:
    reservation_id = os.environ['VELOCITY_PARAM_RESERVATION_ID'].strip()
    url = os.environ['VELOCITY_PARAM_VELOCITY_API_ROOT'].strip()
    token = os.environ['VELOCITY_PARAM_VELOCITY_TOKEN'].strip()
except TypeError:
    logger.warning(f'Reservation id not found, make sure select the topology from velocity : {error_handling()}')
except:
    logger.warning(f'Unknown error : {error_handling()}')

# print python version
logger.info(f'Python Version : {platform.python_version()}')

# build the end point to get the tbml in string
end_point = 'velocity/api/reservation/v17/reservation/' + reservation_id + '/topology'

logger.info('Authorizing velocity ')
logger.info(f'Reservation id : {reservation_id}')

# create velocity object
velocity = Velocity(urlsplit(url).netloc, token=token)
topology_string = ''

# get the topology tbml string
try :
    tbml_string = velocity.get(end_point)
except:
    logger.warning('No topology found , We are exiting power cycle')
    exit(0)

# toogle power only if you found topology
if tbml_string:
    # parse the topology
    logger.info('Parsing the topology ')
    topology_parse = VelocityTopologyParser(string_to_parse=tbml_string)
    topology_parse.parse_topology

    # collect PDU credentials
    logger.info(f'Collecting PDU credentials from topology parser')
    power_managed = 'false'
    logger.info(f'{topology_parse.resource_list}')

    for resource in topology_parse.resource_list:
        # velocity converts Yes/No to boolean i.e small true/false
        logger.info(f'resource property list {topology_parse.__getattribute__(resource).property_list}')
        try:
            power_managed = topology_parse.__getattribute__(resource).__dict__['PDU Power Saving Enabled']
        except:
            logger.warning(f'Resource {resource} is not PDU managed ')

        if power_managed.lower() == 'true':
            try:
                pdu_dns_name = topology_parse.__getattribute__(resource).__dict__['PDU Hostname']
                pdu_username = topology_parse.__getattribute__(resource).__dict__['PDU Username']
                pdu_password = topology_parse.__getattribute__(resource).__dict__['PDU Password']
                outlet_number = topology_parse.__getattribute__(resource).__dict__['PDU Socket']
            except TypeError:
                logger.warning(f'Check the topology tbml file for PDU credentials {error_handling()}')
            except:
                logger.warning(f'Unknown Error :  {error_handling()}')

            logger.info(f'We have PDU {pdu_dns_name} and outlet {outlet_number}')

            # set cli
            outlet_status_cli = 'olStatus ' + outlet_number + '\n'
            outlet_on_cli = 'olOn ' + outlet_number + '\n'

            # establish ssh session
            logger.info(f'Establishing SSH session on PDU {pdu_dns_name} ')
            ssh = paramiko.SSHClient()

            # load SSH host keys.
            ssh.load_system_host_keys()

            # add SSH host key automatically if needed.
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # ssh Connection using username/password authentication.
            ssh.connect(pdu_dns_name,
                        username=pdu_username,
                        password=pdu_password,
                        port=22,
                        allow_agent=False,
                        look_for_keys=False)
            device_connection = ssh.invoke_shell()

            logger.info(f'Successfully connected {pdu_dns_name}')
            device_connection.recv(12000).decode("utf-8")   # this is required to flush the login status from the buffer

            # pass outlet show status command
            device_connection.send(outlet_status_cli)
            sleep(1)                                        # some devices may need more sleep time

            # read the response and decode in to UTF-8 (ASCII) text, and print
            show_status = device_connection.recv(12000).decode("utf-8")
            logger.info(show_status)

            # if the outlet is off , turn it on
            if 'outlet '+outlet_number+': off' in show_status.lower():
                logger.info(f'Turning on outlet {outlet_number}')
                device_connection.send(outlet_on_cli)
                sleep(1)
                show_status = device_connection.recv(12000).decode('utf-8')
                if 'success' in show_status.lower():
                    logger.info(f'Successfully Turned On outlet {outlet_number}')
                else:
                    logger.warning(f'Failed to Turn On outlet {outlet_number}')

            # check the status
            device_connection.send(outlet_status_cli)
            sleep(1)
            status = device_connection.recv(12000).decode('utf-8')
            logger.info(status)

            logger.info('Closing ssh session')
            # Close connection.
            ssh.close()
        else:
            logger.warning(f'Resource {resource} is not PDU managed ')