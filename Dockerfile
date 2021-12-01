FROM python:3.9.9

EXPOSE 80
WORKDIR /app

COPY vehicle_builder /app/

RUN python -m pip install pip-tools
RUN pip-compile --output-file=requirements/requirements.txt requirements/requirements.in
RUN pip install -r requirements/requirements.txt

CMD ./wait-for-it.sh postgres:5432 && python3 main.py