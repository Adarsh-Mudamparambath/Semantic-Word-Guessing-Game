FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN sed -i '/^torch==/d' requirements.txt \
	&& pip install --no-cache-dir -r requirements.txt \
	&& pip install --no-cache-dir torch==2.4.1+cpu --index-url https://download.pytorch.org/whl/cpu

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
