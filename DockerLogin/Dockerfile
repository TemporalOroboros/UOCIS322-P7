FROM python:3.8
LABEL maintainer="noemail@website.domain"
COPY . /todo
WORKDIR /todo
RUN apt-get install -y python-pip python-dev build-essential
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
CMD ["flaskLogin.py"]
