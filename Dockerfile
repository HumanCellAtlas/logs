FROM ubuntu:trusty

RUN apt-get update -y && apt-get upgrade -y && apt-get -y install zip nodejs npm python-pip python-dev build-essential jq
RUN pip install --upgrade pip
RUN pip install awscli
RUN pip install boto3

CMD ["bash"]
