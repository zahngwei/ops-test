FROM python3.8-alpine
COPY . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD ["python","zhc_ktgj_online_probe_monitor_exportor.py","8080"]
