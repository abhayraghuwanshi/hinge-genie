FROM python:3.10

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y tesseract-ocr adb && \
    pip install pytesseract subprocess openai pyyaml Pillow

CMD ["python", "main.py"]
