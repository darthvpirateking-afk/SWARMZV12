# UI Dockerfile
FROM node:20
WORKDIR /ui
COPY . .
RUN npm install
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]