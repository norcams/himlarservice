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
pidfile=/var/tmp/access-daemon.pid
workingdir=$HOME/dev/himlarservice
log_file=/tmp/access-daemon.log
```
