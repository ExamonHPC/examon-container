#!/etc/examon_deploy/examon/scripts/ve/bin/python
"""

    MQTT to Kairosdb connector 
    
    Created on Tue Apr 16 18:37:37 2019
    
    @author:francesco.beneventi@unibo.it
    
    (c) 2019 University of Bologna, [Department of Electrical, Electronic and Information Engineering, DEI]
    
"""

import sys
import json
import time
import math
import copy
import signal
import datetime
import threading

import multiprocessing as mp

from Queue import Empty
from setuptools_scm import get_version
from examon.plugin.examonapp import ExamonApp
from examon.db.kairosdb import KairosDB
from examon.transport.mqtt import Mqtt
from multiprocessing.queues import SimpleQueue



def msg_rate():
    global stats_msg_cntr
    #print " Message rate: {0} msg/s {1}".format(stats_msg_cntr, '\033[1A\r')
    if verbose:
        logger.debug("MQTT message rate: {0} msg/s".format(stats_msg_cntr))
    stats_msg_cntr = 0


def flush_db():
    for _ in range(int(args.w)):
        msg_queue.put(('','__FLUSH',))

    
def timer_handler(t,f,*args):
    while True:
        f(*args)
        time.sleep(float(t))

        
def flush_db_worker(kd):
    global lock
    global data_len
    global metrics_db

    lock.acquire()
    if data_len > 0:
        logger.debug("%s: Worker: [%s] - metrics_db size %d - Number of points: %d " % (datetime.datetime.now(), mp.current_process().name, len(metrics_db.values()), data_len))
        if verbose:
            logger.debug("Db payload: %s" % json.dumps(metrics_db.values(), indent=4))
        kd.put_metrics(metrics_db.values())
        for k,v in metrics_db.iteritems():
            metrics_db[k]['datapoints'] = []
        data_len = 0
    lock.release()
    

def worker_http(conf, data_queues_index):
    global lock
    global data_len
    global metrics_db
    
    topic_db = {}

    def _cast_value(value):
        try:
            value = float(value)
        except:
            value = str(value)
        return value
        
    def _is_valid(tpc):
        ret = ''
        if (len(tpc) % 2) == 0:
            ret += "Uncorrect size, "
        if not "plugin" in tpc:
            ret += "Missing plugin tag, "
        if not "chnl" in tpc:
            ret += "Missing chnl tag, "
        if "" in tpc:
            ret += "Missing field, "
        if ret == '':
            ret = 'Valid'
        return ret

    try:
        kd = KairosDB(conf['K_SERVERS'], conf['K_PORT'], conf['K_USER'], conf['K_PASSWORD'])
        kd.put_metrics(metrics_db.values())
    except:
        logger.error("Couldn't connect to %(server)s on port %(port)s" % {'server': conf['K_SERVERS'], 'port': conf['K_PORT']},exc_info=True)
        sys.exit(1)    
    
    logger.info("Succesfully connected to %(server)s on port %(port)s" % {'server': conf['K_SERVERS'], 'port': conf['K_PORT']})
    
    timerThread2 = threading.Thread(target=timer_handler, args=(conf['FLUSH_TO_DB_INTERVAL_S'], flush_db_worker, kd))
    timerThread2.daemon = True
    timerThread2.start()
    
    logger.info("Entering main loop...")
    while 1:
        try:
            topic, payload = msg_queue[data_queues_index].get()
        except Empty:
            lock.acquire()
            if data_len > 0:
                logger.info("Flush in timeout")
                kd.put_metrics(metrics_db.values())
                for k,v in metrics_db.iteritems():
                    metrics_db[k]['datapoints'] = []
                data_len = 0
            lock.release()
            continue           
        if payload == "CK":
            continue
        if payload == "__FLUSH":
            lock.acquire()
            if data_len > 0:
                logger.info("Flush in timeout")
                kd.put_metrics(metrics_db.values())
                for k,v in metrics_db.iteritems():
                    metrics_db[k]['datapoints'] = []
                data_len = 0
            lock.release()
            continue
        
        try:   
            payload = payload.split(';')
            timestamp = str(math.trunc(float(payload[1])*1000))
        except:
            logger.warning("Malformed payload in message: %s - %s" % (topic, payload), exc_info=True)
            continue
        
        value = _cast_value(payload[0])
        if type(value) == str:
            topic = topic + '__string__'

        lock.acquire()
        try:
            metrics_db[topic]['datapoints'].append([timestamp, value])
            data_len +=1
        except KeyError as e:
            tpc = topic.split('/')
            ret = _is_valid(tpc)
            if ret != 'Valid':
                logger.warning("Invalid topic: %s - %s" % (topic, ret))
                lock.release()
                continue
            tags_tpc = dict()
            for k in range(0, len(tpc)-2, 2):
                tags_tpc[tpc[k]] = tpc[k+1]
            tags_str = ''
            for k, v in tags_tpc.iteritems():
                tags_str += ' %s=%s' % (k, v,)
            topic_db[topic] = {}
            topic_db[topic]['tags'] = tags_str
            topic_db[topic]['metric_name'] = tpc[-1].replace('__string__','')
            tags = topic_db[topic]['tags']
            metric_name = topic_db[topic]['metric_name']   
            
            metrics_db[topic] = {}
            metrics_db[topic]['name'] = metric_name
            metrics_db[topic]['tags'] = copy.deepcopy(tags_tpc)
            metrics_db[topic]['datapoints'] = []
            if type(value) == str:
                metrics_db[topic]['type'] = 'string'
            
            metrics_db[topic]['datapoints'].append([timestamp, value])   
            data_len +=1
        lock.release()
            
    
def worker_mqtt(conf, intopic, data_queues_index):

    def process(client,msg):
        global stats_msg_cntr
        msg_queue[data_queues_index].put((msg.topic,msg.payload,))
        stats_msg_cntr +=1
      
    mqtt = Mqtt(conf['MQTT_BROKER'], conf['MQTT_PORT'], intopic=intopic)
    mqtt.process = process
    
    # stats thread
    statThread = threading.Thread(target=timer_handler,args=(1,msg_rate,))
    statThread.daemon = True
    statThread.start()
    
    mqtt.run()
    
    statThread.join()
    signal.pause()


if __name__ == '__main__':

    app = ExamonApp()
    app.cfg.parser.add_argument("--num-workers", dest='NUM_WORKERS', help="Number of workers")
    app.cfg.parser.add_argument("--flush-interv", dest='FLUSH_TO_DB_INTERVAL_S', help="Number of seconds to wait before writing to the db")
    app.cfg.parser.add_argument('--verbose', dest='VERBOSE', action='store_true', default=False, help='More debug logs (default: False)')
    app.parse_opt()

    print "Config:"
    print json.dumps(app.conf, indent=4)
    
    logger = app.logger
    stats_msg_cntr = 0
    metrics_db = {}
    data_len = 0
    lock = threading.Lock()     
    msg_queue = []
    verbose = app.conf["VERBOSE"]
    topic_list = app.conf['MQTT_TOPIC'].split(',')
    
    for i,t in enumerate(topic_list):
        msg_queue.append(SimpleQueue())
        app.add_worker(worker_mqtt, app.conf, t, i)   
        for _ in range(int(app.conf['NUM_WORKERS'])):  
            app.add_worker(worker_http, app.conf, i)
            
    app.run()    
