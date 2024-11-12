# himlarservice

## Install

```
git clone ..
cd himlarservice
virtualenv --clear .
source bin/activate
pip install -r requirements.txt
```

## Run

To run as root:

```
./access.py start
```

To run as unprivileged user update `services.ini` with something like this:

```
[access-service]
pidfile=/tmp/test_app.pid
log_path=./logs/
loglevel=DEBUG
himlarcli_config=/etc/himlarcli/config.ini
```

`pidfile` and `log_path` needs to writable able by the unprivileged user and
`himlarcli_config` needs to have a ``[rabbitmq]` section pointing to (vagrant)-mq-01
