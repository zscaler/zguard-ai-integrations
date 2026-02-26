FROM ghcr.io/berriai/litellm:main-stable

USER root
RUN pip install --no-cache-dir zscaler-sdk-python
COPY aiguard_guardrail.py /app/aiguard_guardrail.py
