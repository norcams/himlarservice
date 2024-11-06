#!/usr/bin/env python

import json

from himlarcli.keystone import Keystone
from himlarcli.mqclient import MQclient
from himlarcli.service import HimlarService
from himlarcli.service import HimlarServiceError
from himlarcli import utils as himutils


def process_message(ch, method, properties, body):
    #pylint: disable=E0606,W0613

    # TODO: this dos not work for some reason, might break the service after token expires!
    # kc = Keystone(config_path=app.himlarcli_config, debug=app.debug, log=app.logger)
    # kc.set_domain('dataporten')

    ch.basic_ack(delivery_tag=method.delivery_tag)

    data = json.loads(body)
    user = app.kc.get_user_by_email(data['email'], user_type='api')
    app.logger.info('=> processing %s for %s', data['action'], data['email'])

    if user:
        if data['action'] == 'reset_password':
            app.kc.reset_password(email=data['email'], password=data['password'])
        elif data['action'] == 'provision':
            app.logger.warning('=> user exists! %s', data['email'])
    else:
        if data['action'] == 'provision':
            app.kc.provision_dataporten(email=data['email'], password=data['password'])
        elif data['action'] == 'reset_password':
            app.logger.warning('=> Provisioning is required! %s', data['email'])

class TestApp():

    name = 'access-service'
    debug = True

    def __init__(self, config_file='services.ini'):
        self.config = himutils.get_config(config_file)
        self.pidfile_timeout = 2
        self.pidfile_path = himutils.get_config_entry(self.config, self.name, 'pidfile',
                                                      default=f'/var/log/{self.name}.log')
        self.working_directory = himutils.get_config_entry(self.config, self.name, 'workingdir',
                                                           default='/opt/himlarservice')
        self.himlarcli_config = himutils.get_config_entry(self.config, self.name, 'himlarcli_config',
                                                          default='/etc/himlarcli/config.ini')

        log_path = himutils.get_config_entry(self.config, self.name, 'log_path',
                                             default='/var/log/')

        self.logger = himutils.setup_logger(name='access-service',
                                           log_path=log_path,
                                           debug=self.debug)

        self.kc = Keystone(config_path=self.himlarcli_config, debug=self.debug, log=self.logger)
        self.kc.set_domain('dataporten')

    def run(self):
        mq = MQclient(self.himlarcli_config, debug=self.debug, log=self.logger)
        channel = mq.get_channel(queue='access')
        channel.basic_consume(on_message_callback=process_message, queue='access')

        self.logger.info('=> start consuming rabbitmq')
        channel.start_consuming()

if __name__ == "__main__":
    app = TestApp()
    runner = HimlarService(app)
    try:
        runner.do_action()
    except HimlarServiceError as e:
        print(e)
