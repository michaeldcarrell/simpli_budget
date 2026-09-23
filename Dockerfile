FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn simpli_budget.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4 --timeout 120"]
