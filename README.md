# Logs

This repository holds the configuration for the [HCA](https://humancellatlas.org)'s centralized logging, monitoring, and alerting. The design of this system is described in the [DCP Centalized Logging design document](https://docs.google.com/document/d/15RUEodhwS8wtgkIpoJ_6uI9eCErzAw2YXzY6MwwUcG4/edit?usp=sharing).

## Configuration

If this is your first deployment, you will first need to populate [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) with your configuration for the logs project. You can do this with templates using the following command.

```bash
python3 scripts/secret_templates.py
```

Then, configure your logs deployment by modifying the JSON values in each of these secrets. All secrets for the logs project have the prefix `logs/`.

### CI User
To run this repository a CI user must be set up in your AWS account. These are created from the configuration in the `ci` directory.

You don't need to run the commands in this subdirectory yourself, the deployment step should do this for you.

## Environment
First, set the `PROJECT_ROOT` and download the project's secrets with the following commands

```bash
export AWS_PROFILE=<profile>
export GOOGLE_APPLICATION_CREDENTIALS=<credentials.json>
source environment
make secrets
make clean-terraform init
```

## Deployment

The following command will deploy the CI configuration, infrastructure, and apps. In short, everything.
```bash
make deploy
```

## Development

To install the development environment run `make install`.

## Testing

To run unit tests, run `make test`.

## Security

**Please note**: If you believe you have found a security issue, _please responsibly disclose_ by contacting us at [security-leads@data.humancellatlas.org](mailto:security-leads@data.humancellatlas.org).
