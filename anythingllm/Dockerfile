FROM mintplexlabs/anythingllm:latest

USER root

RUN apt-get update && apt-get install -y jq

# Copiar el script de inicialización
COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh

USER anythingllm

# Definir el punto de entrada
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Usar CMD para iniciar AnythingLLM
CMD ["anythingllm", "start"]