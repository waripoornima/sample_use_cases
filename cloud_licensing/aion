###############################################################################
#
#            Spirent TestCenter Traffic Example for Python
#                         by Spirent Communications
#
# Author: Poornima Wari - poornima.wari@spirent.com
#
# Description: This is sample script to demonstrate AION - bgp emulation with bound stream block
#              script need 2 back to back ports on stc
#
###############################################################################

###############################################################################
# Copyright (c) 2021 SPIRENT COMMUNICATIONS OF CALABASAS, INC.
# All Rights Reserved
#
#                SPIRENT COMMUNICATIONS OF CALABASAS, INC.
#                            LICENSE AGREEMENT
#
#  By accessing or executing this software, you agree to be bound by the terms
#  of this agreement.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#  1. Redistribution of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#  2. Redistribution's in binary form must reproduce the above copyright notice.
#     This list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#  3. Neither the name SPIRENT, SPIRENT COMMUNICATIONS, SMARTBITS, nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# This software is provided by the copyright holders and contributors [as is]
# and any express or implied warranties, including, but not limited to, the
# implied warranties of merchantability and fitness for a particular purpose
# are disclaimed. In no event shall the Spirent Communications of Calabasas,
# Inc. Or its contributors be liable for any direct, indirect, incidental,
# special, exemplary, or consequential damages (including, but not limited to,
# procurement of substitute goods or services; loss of use, data, or profits;
# or business interruption) however caused and on any theory of liability,
# whether in contract, strict liability, or tort (including negligence or
# otherwise) arising in any way out of the use of this software, even if
# advised of the possibility of such damage.
#
###############################################################################


from py_velocity_rest_client.Velocity import Velocity               # need it for Velocity ReST instance
from py_velocity_topology_parser.VelocityTopologyParser import VelocityTopologyParser   # need it to parse tbml
from py_spirentaion_rest_client.SpirentAion import SpirentAion      # need it for Spirent Aion ReST instance
from stcrestclient.stcpythonrest import StcPythonRest as StcPython  # need it for STC ReST instance
from urllib.parse import urlsplit  # we need this to parse the url
from urllib.parse import urlunsplit # we need it to build url with http


# helper function
# trace error
def trace_error():
    """
        This definition is to trace the Error
        :return: format to trace the exception
    """
    return 'Error: {}.{},line:{}'.format(sys.exc_info()[0], sys.exc_info()[1],
                                             sys.exc_info()[2].tb_lineno)


import platform     # need it to get the python version
import re           # need it for string match
import base64       # need it to encode username and password
import logging      # need it for velocity logging
import os           # need it to get Velocity environment variables
import sys          # need it for error tracing
import time         # need it for sleep timer


# set the logger format
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.info('Python Version : {}'.format(platform.python_version()))

# get velocity url, reservation id and aion credentials from the velocity environment
try:
    reservation_id = os.environ['VELOCITY_PARAM_RESERVATION_ID'].strip()
    url = os.environ['VELOCITY_PARAM_VELOCITY_API_ROOT'].strip()
    token = os.environ['VELOCITY_PARAM_VELOCITY_TOKEN'].strip()
    aion_server = os.environ['VELOCITY_PARAM_AION_SERVER'].strip()
    aion_user = base64.b64encode(os.environ['VELOCITY_PARAM_AION_USERNAME'].strip().encode("utf-8"))
    aion_password = base64.b64encode(os.environ['VELOCITY_PARAM_AION_PASSWORD'].strip().encode("utf-8"))
    stc_abstract_name = os.environ['VELOCITY_PARAM_STC_ABSTRACT_NAME']
except TypeError:
    logger.critical('Looks like failed to get reservation id! ')
    logger.critical('Make sure you reserve the topology')
    logger.critical(trace_error())
    raise
except:
    logger.critical('Unknown Error {}'.format(trace_error()))
    raise

# build the end point
end_point = '/velocity/api/reservation/v17/reservation/' + reservation_id + '/topology'

logger.info('Authorizing velocity ')
logger.info(f'Topology reservation ID : {reservation_id}')
velocity = Velocity(urlsplit(url).netloc, token=token)
response = velocity.get(end_point)

logger.info('Parsing the topology ')
topology_parse = VelocityTopologyParser(string_to_parse=response)
topology_parse.parse_topology
logger.info('Collecting device credentials from topology parser')

try:
    stc_ip = topology_parse.__getattribute__(stc_abstract_name).ipAddress
    http_server_ip = topology_parse.__getattribute__(stc_abstract_name).LabServer
    stc_port_list = topology_parse.__getattribute__(stc_abstract_name).port_numbers
except TypeError:
    logger.error('Check the tbml file for device credentials {}'.format(error_handling()))
    raise
except:
    logger.error('Unknown Error : {}'.format(error_handling()))
    raise

# topology
txportloc = '//' + stc_ip + '/' + stc_port_list[0]
rxportloc = '//' + stc_ip + '/' + stc_port_list[1]
portlist = '%s %s' % (txportloc, rxportloc)
port1ipv4 = '10.1.1.1'
port2ipv4 = '10.1.1.254'
vlanid = '10'
port1as = '1'
port2as = '100'
drop = 0

# lets upend session name with current time and date
current = datetime.now()
time_date = current.strftime("%H_%M_%S_%m_%d_%Y")

session_name = 'aion' + time_date

# you can comment below line if you installed ReST client with pip
logger.info('Loading Stc ReST Client')
stc = StcPython()

# create session or kill the existing session
logger.info('Creating session {} on {}'.format(http_server_ip, session_name))
stc.new_session(server=http_server_ip, session_name=session_name, existing_session='kill')

# terminate the Lab Server session when the last client disconnects.
stc.perform('TerminateBll', TerminateType='ON_LAST_DISCONNECT')

logger.info('Stc version : {}'.format(stc.get("System1", "Version")))

# connecting to aion
user = base64.b64decode(aion_user.decode("utf-8"))
password = base64.b64decode(aion_password.decode("utf-8"))

logger.info('Connecting to AION {}'.format(aion_server))

if aion_server:
    try:
        stc.perform('TemevaSignInCommand',
                    server=aion_server,
                    username=username,
                    password=password)
    except Exception:
        print('SSL certificate verification failed, we wll try with http')
        content = urlparse(aion_server)
        # dns name will be considered as path
        url = urlunsplit(('http', content.path, '', '', ''))
        if content.netloc:
            url = urlunsplit(('http', content.netloc, content.path, content.params, content.query))
        stc.perform('TemevaSignInCommand',
                    server=url,
                    username=username,
                    password=password)

logger.info('Loading Aion ReST Client')
aion_object = SpirentAion(aion_server, user.decode(), password.decode())
aion_version = aion_object.get('/lic/version')['build_number']
logger.info('Aion Version :{}'.format(aion_version))

# get organization id and user id
organization_id = aion_object.get('/iam/organizations/default')['id']
user_dict = aion_object.get('iam/users/my')
user_id = user_dict['id']
user_email = user_dict['email']

# get stc application id
application_id = ''
end_points = '/inv/products'
product_list = aion_object.get(end_points)
for product_dict in product_list:
    if product_dict['name'] == 'Spirent TestCenter':
        application_id = product_dict['id']

# get the license checkouts
checkout_params = {
                    'view': 'current',
                    'organization_id': organization_id,
                    'application_id': application_id,
                    'user_id': user_id
                }
end_points = 'lic/checkouts'
current_checkouts = aion_object.get(end_points, params=checkout_params)

logger.info('Current Checkouts {}'.format(current_checkouts))

# instruct the API to not display all commands to STDOUT.
stc.config('AutomationOptions', logTo='stcapi.log', logLevel='INFO')

# create project
logger.info('Creating project')
hproject = stc.create("project")

# create port
logger.info('Creating ports')
port1 = stc.create("port", under=hproject, location=txportloc, useDefaulthost=False)
port2 = stc.create("port", under=hproject, location=rxportloc, useDefaulthost=False)

# attach port
logger.info('Reserving Ports {} {} '.format(stc.get(port1, 'location'), stc.get(port2, 'location')))
status = stc.perform("AttachPorts")
logger.info('Successfully reserved the ports')

# get the current checkouts
current_checkouts = aion_object.get(end_points, params=checkout_params)
logger.info('Current Checkouts {}'.format(current_checkouts))

if current_checkouts:
    for checkout_dict in current_checkouts:
        for license in checkout_dict['licenses']:
            logger.info('Checkouts {}'.format(license))

# apply
logger.info('Executing stc.apply()')
stc.apply()

# get the current checkouts
current_checkouts = aion_object.get(end_points, params=checkout_params)
if current_checkouts:
    for checkout_dict in current_checkouts:
        for license in checkout_dict['licenses']:
            logger.info('Checkouts {}'.format(license))

# create emulated device
logger.info('Creating emulated device')
hdeviceport1 = stc.perform("DeviceCreate", ParentList=hproject, DeviceType="Router", IfStack="Ipv4If EthIIIf",
                           IfCount="1 1", Port=port1)
hdeviceport2 = stc.perform("DeviceCreate", ParentList=hproject, DeviceType="Router", IfStack="Ipv4If EthIIIf",
                           IfCount="1 1", Port=port2)
hdevice1 = hdeviceport1["ReturnList"]
hdevice2 = hdeviceport2["ReturnList"]

# enable BGP protocol
logger.info('Enabling bgp on router')
kwargs1 = {"UsesIf-targets": stc.get(hdevice1, "toplevelif-Targets")}
kwargs2 = {"UsesIf-targets": stc.get(hdevice2, "toplevelif-Targets")}
hbgpport1 = stc.create("BgpRouterConfig", under=hdevice1, AsNum=port1as, DutasNum=port2as, DutIpv4Addr=port2ipv4,
                       **kwargs1)
hbgpport2 = stc.create("BgpRouterConfig", under=hdevice2, AsNum=port2as, DutasNum=port1as, DutIpv4Addr=port1ipv4,
                       **kwargs2)

# configure the addressing information for each device.
stc.config(hdevice1 + ".ethiiif", SourceMac="00:10:00:01:00:01")
stc.config(hdevice1 + ".ipv4if", Address=port1ipv4, Gateway=port2ipv4, PrefixLength=24)

stc.config(hdevice2 + ".ethiiif", SourceMac="00:10:00:01:00:03")
stc.config(hdevice2 + ".ipv4if", Address=port2ipv4, Gateway=port1ipv4, PrefixLength=24)

stc.apply()

# retrieve src and dst binding objects
port1ipv4binding = stc.get(hdevice1, "Children-ipv4if")
port2ipv4binding = stc.get(hdevice2, "Children-ipv4if")

# create BGP route 10 on port1 and 10 on port2
bgproute1 = stc.create('BgpIpv4RouteConfig', under=hbgpport1, AsPath=port1as)
bgproute2 = stc.create('BgpIpv4RouteConfig', under=hbgpport2, AsPath=port2as)
bgproute1ipv4 = stc.get(bgproute1, 'Children-Ipv4NetworkBlock')
bgproute2ipv4 = stc.get(bgproute2, 'Children-Ipv4NetworkBlock')
stc.config(bgproute1ipv4, StartIpList='1.0.0.0', NetworkCount="10", Name='BGP route from 1.0.0.0/24 to 1.0.9.0/24')
stc.config(bgproute2ipv4, StartIpList='1.0.50.0', NetworkCount="10", Name='BGP route from 1.0.50.0/24 to 1.0.59.0/24')
stc.apply()

# create stream
logger.info('Creating Bound Stream blocks')
streamblock1 = stc.create("StreamBlock", under=port1, Name="BgpRouteimix1", ExpectedRxPort=port2,
                          SrcBinding=bgproute1ipv4, DstBinding=bgproute2ipv4, FrameLengthMode='imix')
streamblock2 = stc.create("StreamBlock", under=port2, Name="BgpRouteimix2", ExpectedRxPort=port1,
                          SrcBinding=bgproute2ipv4, DstBinding=bgproute1ipv4, FrameLengthMode='imix')

fld_list = stc.get(hproject, "children-FrameLengthDistribution").split()
fld = fld_list[2]
fldslot_list = stc.get(fld, 'children-framelengthdistributionslot').split()
stc.config(fldslot_list[0], FixedFrameLength=128)
stc.config(fldslot_list[1], FixedFrameLength=576)
stc.config(fldslot_list[2], FixedFrameLength=1500)
stc.config(fldslot_list[3], MaxFrameLength=1500, FixedFrameLength=128, MinFrameLength=128, FrameLengthMode='RANDOM')
stc.config(streamblock1, AffiliationFrameLengthDistribution=fld)
stc.config(streamblock2, AffiliationFrameLengthDistribution=fld)
stc.apply()

# start bgp Device
logger.info('Starting all bgp devices')
status = stc.perform("DevicesStartAll")
logger.info(status["Status"])

# subscribe to realtime results.
logger.info('Subscribing Tx and Rx streamblock results !!! ')

sbrds = stc.subscribe(Parent=hproject, ConfigType="StreamBlock", resulttype="TxStreamBlockResults")
stc.create("ResultQuery", under=sbrds, ResultRootList=hproject, ConfigClassId="StreamBlock",
           ResultClassId="RxStreamBlockResults")

# clear all stats
logger.info('Clearing the stats')
stc.perform("ResultsClearAll")

# start the traffic
logger.info('Starting the traffic')
stc.perform("GeneratorStartCommand")

# refresh the result database
logger.info('Refreshing the result database')

for i in range(5):
    stc.perform("RefreshResultView", ResultDataSet=sbrds)
    for result in stc.get(sbrds, "ResultHandleList").split():
        regex = re.compile("txstreamblockresults.")
        if re.match(regex, result):
            rxresult = stc.get(result, "associatedresult-Targets")
            parent = stc.get(result, "parent")
            txframerate = stc.get(result, "FrameRate")
            rxframerate = stc.get(rxresult, "FrameRate")
            txframecount = stc.get(result, "FrameCount")
            rxframecount = stc.get(rxresult, "FrameCount")
            droppedcount = stc.get(rxresult, "DroppedFrameCount")
            logger.info('{} Tx Cnt={} RxCnt={} Tx Frame Rate={} Rx Frame Rate={} '
                        'Dropped Cnt={}'.format(stc.get(parent, 'name'), txframecount,
                        rxframecount, txframerate, rxframerate, droppedcount))

            if int(droppedcount) > 0 or int(rxframecount) == 0:
                drop = 1

            time.sleep(1)

# collect the current checkouts
current_checkouts = aion_object.get(end_points, params=checkout_params)
if current_checkouts:
    for checkout_dict in current_checkouts:
        for license in checkout_dict['licenses']:
            logger.info('Checkouts {}'.format(license))

# stop the traffic
logger.info('Stopping the traffic')
stc.perform("GeneratorStopCommand")

# stop all devices
logger.info('Stopping all bgp devices')
status = stc.perform("DevicesStopAll")
logger.info(status["Status"])

# unsubscribing the results
stc.unsubscribe(sbrds)

# release ports
logger.info('Releasing ports {} {}'.format(txportloc, rxportloc))
release_status = stc.perform("ReleasePort", portlist=[port1, port2])
logger.info('Successfully released the ports')

# get the current checkouts
current_checkouts = aion_object.get(end_points, params=checkout_params)
logger.info('Current Checkouts {}'.format(current_checkouts))

if int(drop) > 0:
    logger.critical('Finished: FAILED')
else:
    logger.info('Finished: PASSED')
