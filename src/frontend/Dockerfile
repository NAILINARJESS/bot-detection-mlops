# Frontend simple avec Nginx
FROM nginx:alpine

# Supprimer le contenu par défaut
RUN rm -rf /usr/share/nginx/html/*

# Copier les fichiers frontend
COPY . /usr/share/nginx/html

# Exposer le port 80
EXPOSE 80

# Lancer Nginx
CMD ["nginx", "-g", "daemon off;"]

