FROM ubuntu:17.10

# Install.
RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential && \
  apt-get install -y software-properties-common && \
  apt-get install -y byobu curl git htop man unzip vim wget jq && \
  apt-get install -y nodejs npm && \
  rm -rf /var/lib/apt/lists/*

#RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
#RUN apt-get install -y npm

# Set environment variables.
ENV HOME /root

# Define working directory.
WORKDIR /root

# Define default command.
CMD ["bash"]
