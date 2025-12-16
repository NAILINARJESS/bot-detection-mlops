# Utiliser l'image officielle k6
FROM loadimpact/k6:latest

# Passer en root pour installer curl
USER root

# Installer curl
RUN apk add --no-cache curl

# Repasser à l'utilisateur k6
USER k6

# Définir le point d'entrée par défaut (optionnel)
WORKDIR /scripts
