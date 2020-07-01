# MSSQL_app
Models are defined in [models.py](models.py)

Main program and logic is in [gui.py](gui.py)

## [Requirements](req.txt)


```astroid==2.4.2
autopep8==1.5.3
Babel==2.8.0
debugpy==1.0.0b11
isort==4.3.21
lazy-object-proxy==1.4.3
mccabe==0.6.1
pycodestyle==2.6.0
pylint==2.5.3
pymssql==2.1.4
pytz==2020.1
six==1.15.0
tkcalendar==1.6.1
toml==0.10.1
typed-ast==1.4.1
wrapt==1.12.1
```

## Configuration
Configuration file for connecting to MSSQL DB is [config.ini](config.ini).
File is in following format:

```
[CONNECTION_SETTINGS]
dbhost = localhost
dbname = OdooExchangeSync
dbuser = SA
dbpass = <YourStrong@Passw0rd>
```