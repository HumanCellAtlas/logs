# Logs

This repository holds the configuration for the [HCA](https://humancellatlas.org)'s centralized logging, monitoring, and alerting. The design of this system is described in the [DCP Centalized Logging design document](https://docs.google.com/document/d/15RUEodhwS8wtgkIpoJ_6uI9eCErzAw2YXzY6MwwUcG4/edit?usp=sharing).

## Deployment

### Environment
First, set the `PROJECT_ROOT` and download the project's secrets with the following commands

```bash
export AWS_PROFILE=<profile>
export GOOGLE_APPLICATION_CREDENTIALS=<credentials.json>
export GCLOUD_PROJECT=<project_id>
source environment
make secrets
make clean-terraform init
```

### Deployment

The following command will deploy the CI confuration, infrastructure, and apps. In short, everything.
```bash
make deploy
```

## CI User
To run this repository a CI user must be set up in your AWS account. These are created from the configuration in the `ci` directory.

You don't need to run the commands in this subdirectory yourself, the `make deploy` command should do this for you.

## Development

To install the development environemnt run `make install`.

## Testing

To run unit tests, run `make test`.

## Deploy

To deploy all applications run `make <stage>-deploy`.
