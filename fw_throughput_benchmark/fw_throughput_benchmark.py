"""

   Sample Cyberflood Test execution Example for Python
         by Spirent Communications

   Author: Poornima Wari - poornima.wari@spirent.com
   Date: March 2021

   Description: This is a simple example to execute existing cyberflood test
               and log the stats using CyberFlood ReST Client

   Way to execute :
       python3 fw_throughput_benchmark.py fw_version cf_test device_type cf_min_score fw_abstract_name cf_abstract_name 
       Ex: python3 fw_throughput_benchmark.py  9.1.4 BW_test paloalto_panos 80 FW-1 TG-CTRL-1

"""


import sys
import time
import logging
import os
from urllib.parse import urlunsplit, urlencode


def execute_cf_test(test_dict):
    """
    execute the test and return the test run dictionary, once the test is complete.
    :rtype: object
    :param test_dict: test dictionary
    :return: test run dictionary
    """
    # We need it for test run id
    test_run_dict = {}
    if test_dict and test_dict["id"]:
        logger.info("Starting Test '" + test_dict["name"] + "' (" + test_dict["type"] + ")...")
        test_run_dict = cf.perform("startTest", testId=test_dict["id"])

        # Wait for test to start
        time.sleep(2)
        run_id = test_run_dict.get("id", None)
        if run_id:
            # Wait for the test to finish.
            stop = False
            while not stop:
                test_run_dict = cf.perform("getTestRun", testRunId=run_id)
                stop = True
                status = test_run_dict.get("status", None)
                if status == "running":
                    time_remaining = test_run_dict.get("timeRemaining", "N/A")
                    logger.info("Test is running " + str(time_remaining) + " seconds remaining...")
                    stop = False
                elif status == "waiting":
                    logger.info("Test is Waiting ...")
                    stop = False
                else:
                    logger.info("Test status " + status)
                time.sleep(5)
    else:
        logger.error("Test run id doesnt exist ")
    return test_run_dict

# return the result URL
def build_url(scheme, netloc, test_run_dict):
    """
      Builds the URL based on the components
      std url format: <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
    :param controller_ip: cyberflood controller ip
    :param test_run_dict: test run dictionary
    :return: returns the results URL
    """

    result_list = cf.perform("listTestRunResults", testRunId=test_run_dict['id'])
    fragment = f"results/{result_list[0]['test']['type']}/{test_run_dict['runId']}"

    return urlunsplit((scheme,netloc,'','',fragment))

# return gare grade and score
def get_grade(test_run_dict):
    """

    :param test_run_dict: test run dictionary
    :return: returns the grade and min score
    """
    test_grade = test_run_dict['grade']
    test_score = test_run_dict['score']

    return (test_grade, test_score)

def error_handling():
    """
        This definition is to trace the Error
        :return: format to trace the exception
    """
    return 'Error: {}.{},line:{}'.format(sys.exc_info()[0], sys.exc_info()[1],
                                             sys.exc_info()[2].tb_lineno)


#Cyberflood Wrapper path
cf_path = os.getcwd() +"/lib/cbfloodPythonReST"
lib_path = os.getcwd() +"/lib"

#set the logger format
logging.basicConfig(
    format = "%(asctime)s %(levelname)-8s %(message)s",
)

# set custom loglevel number
logging.OK = 5  # important
logging.addLevelName(logging.OK, 'OK')      # new log level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.ok = lambda msg, *args: logger._log(logging.OK, msg, args)

# Read all parameters from environment
try:
    fw_name = os.environ['VELOCITY_PARAM_FW_Abstract_name']
    fw_version = os.environ['VELOCITY_PARAM_Fw_version']
    cf_name = os.environ['VELOCITY_PARAM_CF_resource_name']
    cf_test = os.environ['VELOCITY_PARAM_Test_Name']
    cf_test_min_score = os.environ['VELOCITY_PARAM_Min_Score']
    device_type = os.environ['VELOCITY_PARAM_Device_type']
    # This code is option, in case you want to add new parameter for Testname.
    # Make sure key "New_Test" matchs with velocity parameter
    new_key = 'VELOCITY_PARAM_New_Test'
    if new_key in os.environ:
        cf_test = os.environ['VELOCITY_PARAM_New_Test']
except TypeError:
    logging.error("CF|FW credentials are not complete \n Check the manifest file " ,error_handling())
except :
    logging.error("Unkown Error ",error_handling())

# load the Cyberflood wrapper
logger.info("Loading Cyberflood ReST Client ")
sys.path.insert(0,lib_path)
sys.path.insert(1,cf_path)

from TopologyParser import TopologyParser
from SessionClass import SessionClass
import CyberFlood

# initiate topology parser
topology_parse = TopologyParser()
topology_dict = topology_parse.parse_topology()

try :
    # firewall dictionary
    fw_dict = {
        "device_type" : device_type,
        "ip" : topology_dict[fw_name]['ip_address'],
        "username" : topology_dict[fw_name]['user_name'],
        "password" : topology_dict[fw_name]['password']
    }

    # cf controller credentials
    cf_ip = topology_dict[cf_name]['ip_address']
    cf_user_name = topology_dict[cf_name]['user_name']
    cf_password = topology_dict[cf_name]['password']
except TypeError:
    logging.error("CF|FW credentials are not complete \n Check the topology file \n",error_handling())
    exit()
except :
    logging.error("CF|FW credentials are not complete \n Check the topology file \n",error_handling())
    exit()

# execute the test, only if current FW version matches with entered version
# show version cli
cmd = 'show system info | match sw-version'

# initiate SessionClass
session = SessionClass(device_dict=fw_dict)

# establish ssh session
ssh_session = session.ssh_shell()

# pass show cli command on shell and collect the response
res = session.show_cli(ssh_session[0], cmd)
current_version = res[cmd].split(':')[1].strip()

# verify firewall version
if str(fw_version) == str(current_version):
    msg = "firmware version matched with expected version %s actual: %s verified" % (str(fw_version), str(current_version))
    logger.ok(msg)

    logger.info(f"Connecting Cyberflood controller {cf_ip}")
    # connect cyberflood controller
    cf = CyberFlood.CyberFlood(username=cf_user_name, password=cf_password, controller_address=cf_ip, log_level="DEBUG")

    # filter the test by name, it gives all matching test lists
    test_list = cf.perform("listTests", filters={"name": cf_test})

    # check for the exact test match from the test list
    test_dict = {}
    for test_d in test_list:
        if test_d['name'] == cf_test:
            test_dict = test_d

    # execute the test if it exists
    if test_dict:
        logger.info(f"Executing test case :  {cf_test}")
        test_run_dict = execute_cf_test(test_dict)
        result_url = build_url('https', cf_ip, test_run_dict)
        grade, score = get_grade(test_run_dict)
        logger.info(f"Summary result URL : {result_url}")
        logger.info(result_url)
        logger.info(f"Grade : {grade}({score})")
        if int(score) >= int(cf_test_min_score):
            logger.ok("Score verified")
            logger.info("Finished: PASSED")
        else:
            logger.info("Finished : FAILED ")
            logger.error(f"Expected CF test min score is : {cf_test_min_score} and Actual score is : {score}")
    else:
        logger.info("Finished: FAILED")
        logger.critical(f"Test Name {cf_test} doesn't exist ")
else:
    logger.critical(f"Incorrect Firmware version.. expected version : {fw_version}  Current version :{current_version}")
