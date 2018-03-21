# Logs

This repository holds the configuration for HCA'a centralized logging, monitoring, and alerting. The design of this system is described in the [DCP Centalized Logging design document](https://docs.google.com/document/d/15RUEodhwS8wtgkIpoJ_6uI9eCErzAw2YXzY6MwwUcG4/edit?usp=sharing).

## Installation

### Environment
First define all required variables in the `config/environment.template`.

Make sure to specify `GOOGLE_APPLICATION_CREDENTIALS` with _non-privileged_
test credentials.

Once you have specified all of these credentials, source the environment.

### CI User
To run this repository a CI user must be set up in your AWS account. To do this run the following commands.

First set up terraform for the repo.

```bash
make init
```

Then, apply the ci user to your account.

```bash
cd ci
make apply
```

```bash
source config/environment
```

To install the development environemnt run `make install`.

## Testing

To run unit tests, run `make test`.

## Deploy

To deploy all applications run `make deploy`. In the case of failures, check to make sure that all the necessary infrastructure is in place with `./infrastructure.sh plan`.
