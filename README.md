# Zabbix template import

This project was created to make importing multiple zabbix templates easier.

The script contains 1 file, a Python script that uses the pyzabbix library to communicate with the Zabbix API.


## Examples executing script

using commandline arguments to authenticate
```
python template-import.py --api="https://zabbix.something.com" --api-token="b72be8cf163438aacc5afa40a112155e307c3548ae63bd97b87ff4e98b1f7657" template.yaml
```

recursively import all templates in a folder:
```
python template.import.py --api="https://zabbix.something.com" --api-token="b72be8cf163438aacc5afa40a112155e307c3548ae63bd97b87ff4e98b1f7657" -r /templates/
```
Note: any errors will be logged at the end of the script.
