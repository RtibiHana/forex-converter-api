FROM python:3.11-alpine

# Créer un utilisateur non-root pour la sécurité
RUN addgroup -S forexgroup && adduser -S forexuser -G forexgroup

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Changer les permissions
RUN chown -R forexuser:forexgroup /app

# Changer d'utilisateur
USER forexuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]