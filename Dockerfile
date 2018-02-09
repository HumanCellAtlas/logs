FROM ubuntu:trusty

RUN apt-get update -y && apt-get upgrade -y && apt-get -y install python-pip python-dev build-essential
RUN pip install --upgrade pip
RUN pip install awscli

CMD ["bash"]
