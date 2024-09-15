#!/bin/bash

# Iniciar AnythingLLM
{
  cd /app/server/ &&
    npx prisma generate --schema=./prisma/schema.prisma &&
    npx prisma migrate deploy --schema=./prisma/schema.prisma &&
    node /app/server/index.js
} &
{ node /app/collector/index.js; } &

# Esperar a que alguno de los procesos finalice
wait -n
exit $?
