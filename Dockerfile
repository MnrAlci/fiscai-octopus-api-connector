# Optional: run the MCP server in a container. Not required; the plugin normally runs directly with Python.
# Credentials are passed at run time, never baked into the image:
#   docker run -i --rm -e OCTOPUS_SOFTWARE_HOUSE_UUID -e OCTOPUS_USER -e OCTOPUS_PASSWORD fiscai-octopus-api-connector
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server ./server
RUN useradd --create-home app
USER app
ENTRYPOINT ["python", "server/run_cli.py", "serve"]
