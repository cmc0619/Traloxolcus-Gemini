FROM nginx:alpine

RUN apk add --no-cache openssl

COPY conf.d/app.conf /etc/nginx/conf.d/app.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && sed -i 's/\r$//' /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
