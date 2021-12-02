FROM python:3.9.9

WORKDIR /opt/app
RUN mkdir -p /opt/app
COPY app /opt/app
RUN pip install -r requirements/requirements.txt
ENV PYTHONPATH='/opt'