FROM python:3.8
LABEL maintainer=ekillen@uoregon.edu
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /api_test
WORKDIR /api_test
RUN pip install -r requirements.txt
CMD ["python -u api_test.py"]
