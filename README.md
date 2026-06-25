# RelayPOP

RelayPOP is a lightweight Dockerized Python web application that retrieves messages from POP3 mailboxes and forwards them to an SMTP server.

It provides a simple web interface to manage POP3 accounts, SMTP profiles, scheduling intervals, message retention policies, and delivery status.

## Features

* POP3 mail retrieval
* SMTP forwarding
* Multiple POP3 accounts
* Multiple SMTP profiles
* Scheduled polling
* Manual polling
* Delivery logging
* Web-based administration
* Lightweight SQLite backend
* Docker deployment

## Build

Clone this repository and build the Docker image:

```bash
docker build -t local/relaypop:1.0 .
```

## Docker Compose

Example compose configuration:

```yaml
services:

  relaypop:

    image: local/relaypop:1.0

    container_name: relaypop

    restart: unless-stopped

    environment:
      TZ: Europe/Rome
      SECRET_KEY: change_me

    ports:
      - "8080:8080"

    volumes:
      - /var/lib/docker/data/relaypop/config:/config
      - /var/lib/docker/data/relaypop/data:/data
```

## Volumes

| Container Path | Description                      |
| -------------- | -------------------------------- |
| /config        | Application configuration        |
| /data          | SQLite database and runtime data |

## Default Access

After startup, open:

```
http://your-server:8080
```

Configure your POP3 accounts and SMTP profiles from the web interface.

The default credentials for the first login are: admin / popre1ay

You can change after in the settings menù.

## Notes

RelayPOP is designed primarily for home labs, legacy POP3 environments, and small mail-forwarding scenarios where messages must be collected from POP3 mailboxes and delivered to another SMTP infrastructure.
