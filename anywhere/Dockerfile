FROM ubuntu:latest
MAINTAINER ColinBin "colinlvbin@gmail.com"
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip
COPY . /anywhere
WORKDIR /anywhere
RUN pip3 install -r ./requirements.txt
ENTRYPOINT ["python3.6"]
CMD ["./app.py"]
