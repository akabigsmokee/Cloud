FROM ubuntu

ARG PASSWORD

# Install required packages
RUN apt-get update && apt-get install -y openssh-server net-tools curl passwd

# Install ZeroTier dependencies
RUN apt-get install -y libcurl4 libcap2 build-essential

# Set the password for the root user
RUN echo "root:${PASSWORD}" | chpasswd

# Configure SSH server
RUN mkdir /var/run/sshd
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
