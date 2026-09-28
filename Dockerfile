FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true
COPY . .
EXPOSE 7860
CMD ["python", "src/dashboard/web_app.py"]
