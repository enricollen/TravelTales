FROM python:3.10.6

WORKDIR /Server
ADD . .

# install audio format converter dependendencies 
#RUN apk install ffmpeg
RUN apt-get -y update
#RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN pip install -r requirements.txt

#CMD [ "waitress-serve", "--host", "0.0.0.0", "--port", "8080", "app:app"]
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "--certfile", "/host-ssl-dir/fullchain.pem", "--keyfile", "/host-ssl-dir/privkey.pem", "server:app"]