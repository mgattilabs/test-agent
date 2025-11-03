FROM python:3.11
WORKDIR /app
COPY . .
COPY .env.example .env
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "main.py"]