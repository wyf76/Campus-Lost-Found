# Build the React/Vite frontend.
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

# Run Django and serve the built frontend from the same origin.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
COPY --from=frontend-build /frontend/dist ./dist

CMD ["sh", "-c", "DATABASE_URL=\"${DATABASE_URL_UNPOOLED:-$DATABASE_URL}\" python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
