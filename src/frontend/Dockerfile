FROM nginx:alpine

# Supprime les fichiers par défaut
RUN rm -rf /usr/share/nginx/html/*

# Copier seulement le build frontend (HTML/JS/CSS)
COPY build/ /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

