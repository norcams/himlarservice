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
import utils

def action_status():
    plf = PIDLockFile(pidfile)
    pid = plf.is_locked()
    logger.info('status pid %s' % pid)
    if pid:
        print '%s: running, PID = %s' % (sname, pid)
    else:
        print '%s: NOT running' % (sname)

def action_stop():
    logger.info('stopping: %s', sname)
    plf = PIDLockFile(pidfile)
    pid = plf.is_locked()
    if pid:
        logger.info('kill pid %s', pid)
        os.kill(pid, signal.SIGTERM)
    else:
        print "%s: NOT running" % sname

def action_restart():
    logger.info('restart: %s', sname)
    action_stop()
    action_start()

def action_start():
    logger.info('starting: %s', sname)
    try:
        with ctx:
            run_consumer()
    except:
        sys.exit(1)

#pylint: disable=W0613
def shutdown(signum, frame):  # signum and frame are mandatory
    logger = logging.getLogger(sname)

    #print frame.f_globals
    logger.info('shutdown %s %s', signum, frame)

    # Close rabbitmq connection
    frame.f_globals['BaseConnection'].close()

    # Remove pid file
    os.unlink(pidfile)
    sys.exit(0)

# pylint: disable=W0613
def process_action(ch, method, properties, body): #callback
    ch.basic_ack(delivery_tag=method.delivery_tag)

    logger = logging.getLogger(sname)
    kc = Keystone(config_path=himlarcli_config, debug=options.debug, log=logger)
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

def run_consumer():
    logger = utils.get_logger(name=sname,
                              log_file=log_file,
                              debug=options.debug,
                              loglevel=loglevel)

    mq = MQclient(himlarcli_config, debug=options.debug, log=logger)
    channel = mq.get_channel('access')
    channel.basic_consume(process_action, queue='access')

    logger.info('start consuming rabbitmq')
    channel.start_consuming()

if __name__ == "__main__":

    # Name
    sname = 'access-service'

    # Set up parser
    parser = Parser(name=sname,
                    description='access service daemon',
                    autoload=False)
    parser.toggle_show('dry-run')
    parser.toggle_show('format')
    parser.toggle_show('config')
    parser.add_actions({'start': 'start',
                        'stop': 'stop',
                        'restart': 'restart',
                        'status': 'status'})
    parser.add_opt_args({'-f': {'sub': 'start',
                                'dest': 'foreground',
                                'const': True,
                                'default': False,
                                'action': 'store_const'}})
    options = parser.parse_args()

    # Config with defaults that services.ini overrides
    config = himutils.get_config('services.ini')
    log_file = utils.get_config(config, sname, 'log_file', '/var/log/%s.log' % sname)
    loglevel = utils.get_config(config, sname, 'loglevel', 'INFO')
    pidfile = utils.get_config(config, sname, 'pidfile', '/var/run/%s.pid' % sname)
    workingdir = utils.get_config(config, sname, 'workingdir', '/opt/himlarservice')
    himlarcli_config = utils.get_config(config, sname, 'himlarcli_config', '/etc/himlarcli/config.ini')
    signal_map = { signal.SIGTERM: shutdown, signal.SIGPIPE: shutdown, signal.SIGINT: shutdown }
    stdout = sys.stdout if options.debug else None
    stderr = sys.stderr if options.debug else None
    if hasattr(options, 'foreground'):
        detatch = True if not options.foreground else False
    else:
        detatch = True

    # Logger
    logger = utils.get_logger(name=sname,
                              log_file=log_file,
                              debug=options.debug,
                              loglevel=loglevel)

    # Context
    ctx =  daemon.DaemonContext(chroot_directory=None,
                                working_directory=workingdir,
                                signal_map=signal_map,
                                stdout=stdout,
                                stderr=stderr,
                                detach_process=detatch,
                                files_preserve=[log_file],
                                pidfile=PIDLockFile(pidfile, 2.0))

    # Run local function with the same name as the action
    action = locals().get('action_' + options.action)
    if not action:
        himutils.sys_error("Function action_%s() not implemented" % options.action)
    action() # pylint: disable=E1102
