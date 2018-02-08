# Logs

This repository holds the configuration for HCA'a centralized logging, monitoring, and alerting. The design of this system is described in the [DCP Centalized Logging design document](https://docs.google.com/document/d/15RUEodhwS8wtgkIpoJ_6uI9eCErzAw2YXzY6MwwUcG4/edit?usp=sharing).

## Installation

First define all required variables in the `environment`.

Make sure to specify `GOOGLE_APPLICATION_CREDENTIALS` with _non-privileged_
test credentials.

Once you have specified all of these credentials, source the environment.

```bash
source environment
```

To 

## Testing

To run unit tests, run `make test`.

## Deploy

To deploy all applications run `make deploy`. In the case of failures, check to make sure that all the intermediate infrastructure deployment has succeeded.

## Exporing logs

### From GCP to CloudWatch

Add an export from your application to the `logs` sink.

### From CloudWatch Logs to ElasticSearch

Use the `exporters/cwl_to_elk/add_log_group.sh` command.
