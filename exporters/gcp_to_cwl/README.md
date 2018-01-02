# GCP to CloudWatch Logs Exporter

The lambda in this repository enables exporting application logs from GCP into cloudwatch logs. See the diagram below for an architectural overview.

![tree!](https://github.com/HumanCellAtlas/logs/blob/master/static/gcp-exporter.png?raw=true)

Red arrows indicate data being pusshed from the client to the server, blue arrows indicate clients pulling data from a server.

## Development environment

```bash
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```
