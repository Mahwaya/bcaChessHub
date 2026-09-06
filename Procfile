web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2

# No `release:` line on purpose. Nixpacks bakes it into the build image as a
# RUN step, and the build phase has no access to Railway's private network, so
# `migrate` fails there with:
#   could not translate host name "postgres.railway.internal" to address
# Migrations run at runtime instead, via the startCommand in railway.toml,
# where the internal hostname resolves correctly.
