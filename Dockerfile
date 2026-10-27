FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE DATA-LICENSE.md ./
COPY deepmentor ./deepmentor
COPY open_mentor ./open_mentor
RUN pip install --no-cache-dir '.[bots]' && useradd --create-home --uid 10001 mentor && mkdir /state && chown mentor /state
USER mentor
ENV PYTHONUNBUFFERED=1
EXPOSE 8767
ENTRYPOINT ["python", "-m", "deepmentor", "--state-dir", "/state"]
CMD ["bot", "--port", "8767"]
