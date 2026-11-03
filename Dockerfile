FROM  python:3.14.6-alpine 

RUN pip install flask

RUN mkdir /app

COPY app.py book.py logger_config.py /app/

WORKDIR /app

CMD ["python", "app.py"]
