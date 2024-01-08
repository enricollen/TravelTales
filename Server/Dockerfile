FROM python:3.10.6

WORKDIR /Server
ADD . .
RUN pip install -r requirements.txt

RUN python -m nltk.downloader stopwords

#CMD [ "waitress-serve", "--host", "0.0.0.0", "--port", "8080", "app:app"]
CMD [ "gunicorn", "--bind", "0.0.0.0:8080", "--certfile", "/host-ssl-dir/fullchain.pem", "--keyfile", "/host-ssl-dir/privkey.pem", "app:app"]