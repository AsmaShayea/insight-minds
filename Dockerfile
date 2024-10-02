FROM python:3.7-alpine
RUN pip install fastapi uvicorn
COPY ./start.sh /start.sh
RUN chmod +x /start.sh
COPY ./app /app
CMD ["./start.sh"]