FROM postgres:16-alpine

# Copy initialization script
COPY init-db.sh /docker-entrypoint-initdb.d/10-init-db.sh

# Make script executable
RUN chmod +x /docker-entrypoint-initdb.d/10-init-db.sh


