#!/usr/bin/env python

import daemon
import json
import os
import sys
import signal
import time
import logging
from pidlockfile import PIDLockFile
from himlarcli.keystone import Keystone
from himlarcli.mqclient import MQclient
from himlarcli.parser import Parser
from himlarcli import utils as himutils

import logs as log


def action_status():
    logger = logging.getLogger(daemon_name)
    plf = PIDLockFile(pidfile)
    pid = plf.is_locked()
    logger.info('status pid %s' % pid)
    if pid:
        print '%s: running, PID = %s' % (daemon_name, pid)
    else:
        print '%s: NOT running' % (daemon_name)

def action_stop():
    logger.info('stopping: %s', daemon_name)
    plf = PIDLockFile(pidfile)
    pid = plf.is_locked()
    if pid:
        logger.info('kill pid %s', pid)
        os.kill(pid, signal.SIGTERM)
    else:
        print "%s: NOT running" % daemon_name

def action_restart():
    logger.info('restart: %s', daemon_name)
    action_stop()
    action_start()

def action_start():
    logger = logging.getLogger(daemon_name)
    logger.info('starting: %s', daemon_name)
    try:
        with ctx:
            run_daemon()
    except:
        sys.exit(1)

#pylint: disable=W0613
def shutdown(signum, frame):  # signum and frame are mandatory
    #logger = logging.getLogger(daemon_name)

    #print frame.f_globals
    #logger.info('shutdown %s %s', signum, frame)

    # Close rabbitmq connection
    frame.f_globals['BaseConnection'].close()

    # Remove pid file
    os.unlink(pidfile)
    sys.exit(0)

# pylint: disable=W0613
def process_action(ch, method, properties, body): #callback
    ch.basic_ack(delivery_tag=method.delivery_tag)

    logger = logging.getLogger(daemon_name)
    kc = Keystone(config_path=config.get(daemon_name, 'himlarcli_config'), debug=options.debug, log=logger)
    kc.set_domain('dataporten')

    data = json.loads(body)
    user = kc.get_user_by_email(data['email'], user_type='api')

    logger.info('processing %s for %s', data['action'], data['email'])

    if user:
        if data['action'] == 'reset_password':
            reset = kc.reset_password(email=data['email'], password=data['password'])
        elif data['action'] == 'provision':
            logger.info('user exists! %s', data['email'])
    else:
        if data['action'] == 'provision':
            provision = kc.provision_dataporten(email=data['email'], password=data['password'])
        elif data['action'] =='reset_password':
            logger.info('Provisioning is required! %s', data['email'])

def run_daemon():
    logger = log.get_logger(name=daemon_name,
                            log_file=config.get(daemon_name, 'log_file'),
                            debug=options.debug,
                            loglevel=config.get(daemon_name, 'loglevel'))

    mq = MQclient(options.config, debug=options.debug, log=logger)
    channel = mq.get_channel('access')
    channel.basic_consume(process_action, queue='access')

    logger.info('start consuming rabbitmq')
    channel.start_consuming()

    # while True:
    #      logger.info("sample INFO message")
    #      time.sleep(5)

if __name__ == "__main__":

    # Name
    daemon_name = 'access-daemon'

    # Set up parser
    parser = Parser(name=daemon_name,
                    description='access daemon',
                    autoload=False)
    parser.toggle_show('dry-run')
    parser.toggle_show('format')
    parser.add_actions({'start': 'start',
                        'stop': 'stop',
                        'restart': 'restart',
                        'status': 'status'})
    options = parser.parse_args()

    # Config
    config = himutils.get_config('services.ini')

    # Logger
    logger = log.get_logger(name=daemon_name,
                            log_file=config.get(daemon_name, 'log_file'),
                            debug=options.debug,
                            loglevel=config.get(daemon_name, 'loglevel'))

    stdout = sys.stdout #if options.debug else os.devnull
    stderr = sys.stderr #if options.debug else os.devnull
    pidfile = config.get(daemon_name, 'pidfile')

    signal_map = {
         signal.SIGTERM: shutdown,
         signal.SIGPIPE: shutdown,
         signal.SIGINT: shutdown
    }

    ctx =  daemon.DaemonContext(chroot_directory=None,
                                signal_map=signal_map,
                                stdout=stdout,
                                stderr=stderr,
                                pidfile=PIDLockFile(pidfile, 2.0))

    # Run local function with the same name as the action
    action = locals().get('action_' + options.action)
    if not action:
        himutils.sys_error("Function action_%s() not implemented" % options.action)
    action() # pylint: disable=E1102
