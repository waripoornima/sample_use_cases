"""

   Sample SNE Map execution Example for Python
         by Spirent Communications

   Author: Poornima Wari - poornima.wari@spirent.com
   Date: April 2021

   Description: This is a simple example to execute existing SNE map
               and log the stats using stc ReST Client

   Way to execute :
       python3 impairment_map.py

"""


def error_handling():
    """
        This definition is to trace the Error
        :return: format to trace the exception
    """
    return 'Error: {}.{},line:{}'.format(sys.exc_info()[0], sys.exc_info()[1],
                                             sys.exc_info()[2].tb_lineno)

def get_stats(sbrds):
    """
        This definition is to get the stats and store in dataframe
    :param rds: stream block result subscription handle
    :return: Stats Data frame
    """
    stats = []
    columns = ["StreamBlockName",
                 "TxFrameCount",
                 "RxFrameCount",
                 "TxBitRate",
                 "RxBitRate",
                 "TxFrameRate",
                 "RxFrameRate",
                 "DroppedFrameCount",
                 "DroppedFramePercent(%)",
                 "InOrderFrameCount",
                 "AvgLatency(μs)"]

    # enable clear result setting for automatic stop, clear result and restart traffic on all ports
    # below command doesn't stop and start traffic automatically

    stc.perform('ResultsClearAllCommand')
    time.sleep(5)

    for count in range(10):
        stc.perform("RefreshResultView", ResultDataSet=sbrds)
        for txresult in stc.get(sbrds, "ResultHandleList").split():
            regex = re.compile("txstreamblockresults.")
            if re.match(regex, txresult):
                rxresult = stc.get(txresult, "associatedresult-Targets")
                parent = stc.get(txresult, "parent")
                txframecount = stc.get(txresult, "FrameCount")
                rxframecount = stc.get(rxresult, "FrameCount")
                txbitrate = stc.get(txresult, 'BitRate')
                rxbitrate = stc.get(rxresult, 'BitRate')
                tx_frm_rate = stc.get(txresult, 'FrameRate')
                rx_frm_rate = stc.get(rxresult, 'FrameRate')
                avglatency = stc.get(rxresult, 'AvgLatency')
                drop_frame_count = stc.get(rxresult, "DroppedFrameCount")
                drop_frame_percent = stc.get(rxresult, "DroppedFramePercent")
                in_order_frame_count = stc.get(rxresult,"InOrderFrameCount")
                stream_name = stc.get(parent, 'name')
                stats.append([stream_name,txframecount,rxframecount,txbitrate,
                              rxbitrate,tx_frm_rate,rx_frm_rate,drop_frame_count,
                              drop_frame_percent,in_order_frame_count,avglatency])
        time.sleep(1)
    return pd.DataFrame(stats,columns=columns)

def get_sne_map_name(sne_map_json,sne_port_list):
    # read json file
    json_file = open(sne_map_json,'r')

    # store data in json object
    json_object = json.load(json_file)

    # close the original file
    json_file.close()

    # verify for input port and relocate with new port
    # SNE ports are indexed 1- n
    # We need to decrease 1 for port relocation as,
    # When reserving the ports or editing the json, the ports start with 0.
    # When checking the link status, enabling the links, or disabling the links. it starts with 1.
    #           ex : if you want to relocate port to 5,2 you need to update .json with 4,1
    #                   SNE automatically adds 1 -> 5,2
    #

    if json_object['nodes'][0]['type'] == 'NetworkInputPort':
        json_object['nodes'][0]['settings']['networkStartPoint']['port'] = int(sne_port_list[0].split('/')[1]) - 1

    # check for output port and relocate with new port
    if json_object['nodes'][1]['type'] == 'NetworkOutputPort':
        json_object['nodes'][1]['settings']['networkEndPoint']['port'] = int(sne_port_list[1].split('/')[1]) - 1

    # lets upend mapName with current time and date, to make it sne needs unique map name
    now = datetime.now()
    time_date = now.strftime("%H_%M_%S_%m_%d_%Y")
    current_map = json_object['mapName'] + time_date
    json_object['mapName'] = current_map
    current_file = os.path.abspath('latest' + time_date + '.json')
    latest_json = open(current_file,'w')
    json.dump(json_object,latest_json)
    latest_json.close()

    return [current_file, current_map]


import platform
import re                           # we need this for regexp
import time                         # we need this to pause for traffic
import sys                          # we need this to load lib path
import logging                      # we need this for logging message
import json                         # we need this to load the payload for http verb
from urllib.parse import urlsplit   # we need this to split the url
import pandas as pd                 # we need this to decorate the stats
from stcrestclient.stcpythonrest import StcPythonRest as StcPython
import os               # we need to for environment variables
from datetime import datetime
from py_sne_rest_client.SpirentNetworkEmulator import SpirentNetworkEmulator
from py_velocity_rest_client.Velocity import Velocity
from py_velocity_topology_parser.VelocityTopologyParser import VelocityTopologyParser


# set the config_files path
config_path = os.getcwd() + '/config_files/'

# set the logger format for velocity
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
)

# set new loglevel number
logging.OK = 5  # positive yet important
logging.addLevelName(logging.OK, 'OK')  # new log level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.ok = lambda msg, *args: logger._log(logging.OK, msg, args)

######################################################################################################
# Connect to the lab-server
# Setting lab server variables
######################################################################################################
try:
    sne_name = os.environ['VELOCITY_PARAM_SNE_ABSTRACT_NAME'].strip()
    stc_name = os.environ['VELOCITY_PARAM_STC_ABSTRACT_NAME'].strip()
    map_username = os.environ['VELOCITY_PARAM_MAP_USERNAME'].strip()
    map_file_name = os.environ['VELOCITY_PARAM_MAP_FILENAME'].strip()
    token = os.environ['VELOCITY_PARAM_VELOCITY_TOKEN'].strip()
    reservation_id = os.environ['VELOCITY_PARAM_RESERVATION_ID'].strip()
    url = os.environ['VELOCITY_PARAM_VELOCITY_API_ROOT'].strip()
    xml_filename = os.environ['VELOCITY_PARAM_XML_FILENAME'].strip()
    drop_count = os.environ['VELOCITY_PARAM_DROP_COUNT'].strip()
    minutes = os.environ['VELOCITY_PARAM_MINUTES'].strip()
except TypeError:
    logger.error(f'Device basic credentials are not available, check the manifest.json file : {error_handling()}')
except :
    logger.error(f' unknown error : {error_handling()}')

logger.info(f'Python Version : {platform.python_version()}')

# build the end point
end_point = 'velocity/api/reservation/v17/reservation/' + reservation_id + '/topology'

logger.info('Authorizing velocity ')
logger.info(f'Reservation id : {reservation_id}')
velocity = Velocity(urlsplit(url).netloc, token=token)
response = velocity.get(end_point)

logger.info('Parsing the topology ')
topology_parse = VelocityTopologyParser(string_to_parse=response)
topology_parse.parse_topology
logger.info(f'Collecting device credentials from topology parser')

try:
    sne_ip = topology_parse.__getattribute__(sne_name).ipAddress
    sne_username = topology_parse.__getattribute__(sne_name).username
    stc_ip = topology_parse.__getattribute__(stc_name).ipAddress
    http_server_ip = topology_parse.__getattribute__(stc_name).LabServer
    stc_port_list = topology_parse.__getattribute__(stc_name).port_numbers
    sne_port_list = topology_parse.__getattribute__(sne_name).port_numbers
    sne_abstract_ports = topology_parse.__getattribute__(sne_name).port_list
except TypeError:
    logger.error(f'Check the tbml file for device credentials {error_handling()}')
    raise
except :
    logger.error(f'Unknown Error :  {error_handling()}')
    raise

# physical port location
txport_loc = '//' + stc_ip + '/' +stc_port_list[0]
rxport_loc = '//' + stc_ip + '/' +stc_port_list[1]

# set sne .json file path
sne_json_file = config_path + map_file_name

# Initiating SNE ReST Client"
logger.info(f'Initializing SNE : ip - {sne_ip} username - {sne_username}')
sne = SpirentNetworkEmulator(sne_ip, sne_username)

# reverse sne list if port2 is listed 0th element
if '2' in sne_abstract_ports[0]:
    sne_port_list.reverse()

# relocate sne ports and create new .json file
logger.info(f'Relocating SNE ports : {sne_port_list}')
latest_json_file, map_name = get_sne_map_name(sne_json_file, sne_port_list)
logger.info('loading SNE json file')

# load the json file on SNE
end_point = '/maps/json?shareWithAll=false'
load_json_status = sne.post(end_point, file=latest_json_file)
logger.info(f'Status : {load_json_status}')

# get the list of maps
map_list = sne.get('/maps')
maps_dict = map_list['maps']

# filter map_dict for specific map name
result_list = [map_dict for map_dict in maps_dict if map_dict.get('mapName', '') == map_name]
first_result = result_list[0]

# get the map UUID, we need it to execute load, start, stop, etc
map_id = first_result['mapId']
mapid_end_piont = '/maps/' + map_id

# delete the local file after loading it to sne
os.remove(latest_json_file)

# loading STC ReST client
stc = StcPython()
logger.info(f'Connecting to the http server {http_server_ip}')

# kill the existing session if any, and create new session
logger.info(f'Creating STC session : {map_name}')
stc.new_session(server=http_server_ip, session_name=map_name, existing_session='kill')

# Terminate session on last disconnect
stc.perform("TerminateBll", TerminateType="ON_LAST_DISCONNECT")

# get stc version
stc_version = stc.get('System1', 'Version')
logger.info(f'Loaded STC Version : {stc_version}')

# get the SNE build version
sne_version = sne.get('/instrument/software/buildversion')
logger.info(f'SNE version : {sne_version}')
logger.info(f'SNE map : {map_name}')

# reset the config, it will help clear config, if you connected to existing session
stc.perform("ResetConfig", config="system1")

# Load the stc XML
logger.info(f"Loading stc xml {config_path + xml_filename} ")
stc.perform('LoadFromXml', filename=config_path + xml_filename)

# enable stc logging.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# get the project handle
hproject = stc.get("system1", "children-project")

# get the logical port-list.
portlist = stc.get("system1.project", "children-port").split()

# relocate the ports
logger.info(f'Relocating STC ports to : {txport_loc}  {rxport_loc}')
stc.config(portlist[0], location=txport_loc, useDefaultHost=False)
stc.config(portlist[1], location=rxport_loc, useDefaultHost=False)

# Bring the port up
logger.info("Reserving STC ports")
stc.perform('attachports')
logger.info("Ports are now online")

# Subscribe to realtime results.
logger.info("Subscribing streamblock results")
rds = stc.perform('ResultsSubscribeCommand',Parent=hproject, ConfigType="StreamBlock", resulttype="TxStreamBlockResults")
sbrds = rds['ReturnedDataSet']
stc.create('ResultQuery', under=sbrds, ResultRootList=stc.get('system1', 'children-project'), ConfigClassId='StreamBlock', ResultClassId='RxStreamBlockResults')
stc.apply()

# Load the sne map
logger.info(f'Loading sne map : {map_name}')
logger.info(f'UUID - {map_id}')
load_status = sne.post(mapid_end_piont + '/load')
logger.info(f'Status :{load_status}')

# Get the impairment id
impairment_list = sne.get(mapid_end_piont+'/impairments')

# get the impairment dictionary from the response
imps_dict = impairment_list['impairments']

# filter dictionary for Drop Packets
result_list = [imp_dict for imp_dict in imps_dict if imp_dict.get('name', '') == 'Drop Packets']
first_result = result_list[0]

# get the UUID for Drop Packets
imp_id = first_result['impId']

logger.info(f'Sne Drop packet UUID :{imp_id}')
imp_id_end_point = mapid_end_piont + '/impairments/' + imp_id

# we need below assignment as SNE is case sensitive
true = 'true'
false = 'false'

drop_payload = {
  "packetDropMode": 'standardDropMode',
  "enabled": true,
  "timeConstraints": {
    "enableTimeConstraints": false,
    "startDelay": 1000,
    "duration": 5000
  },
  "packetDropSettings": {
    "standardDropMode": {
      "packetDropCount": drop_count,
      "perPacketCount": 100,
      "dropMethod": 'dropEvenly'
    }
  }
}

logger.info('Starting the SNE map')
start_status = sne.put('/maps/' + map_id + '/start')
logger.info(f'Status :{start_status}')

# Start the stream
logger.info('Starting STC traffic')
stc.perform("GeneratorStart")

seconds = int(minutes) * 60
time.sleep(seconds)

# We need below code to display entire dataframe
logger.info('Refreshing and collecting the STC stats')
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    logger.info(get_stats(sbrds))

# change the drop impairment settings
logger.info(f'Changing the SNE drop count to {drop_count}')
packet_drop_status = sne.put(imp_id_end_point + '/packetdrop', payload=drop_payload)
logger.info('Status : {packet_drop_status}')

# clear, refresh and collect the latest stats
logger.info('Refreshing and collecting the STC stats')
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    logger.info(get_stats(sbrds))

# stopping the SNE traffic
logger.info('Stopping SNE traffic')
stop_status = sne.put('/maps/' + map_id + '/stop')
logger.info(f"SNE stop response: {stop_status}")

# unloading the SNE map
logger.info('Unloading the SNE map')
unload_status = sne.put('/maps/' + map_id + '/unload')
logger.info('Status : {unload_status}')

# deleting the SNE map
logger.info(f'Deleting the SNE MAP {map_name} from SNE')
delete_status = sne.delete_map(map_id)
logger.info('Status : {delete_status}')

# unsubscribe results
logger.info('Unsubscribing STC results')
stc.perform('ResultDataSetUnsubscribe', ResultDataSet=sbrds)

# stop the traffic
logger.info('Stopping the STC traffic')
stc.perform("GeneratorStop")

logger.info('Finished: PASSED')
