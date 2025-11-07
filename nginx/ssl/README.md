# SSL Certificates Directory

## Production SSL Certificates

Place your SSL certificates in this directory:

- `fullchain.pem` - Full certificate chain (certificate + intermediates)
- `privkey.pem` - Private key

## Option 1: Let's Encrypt (Recommended)

Use Certbot to obtain free SSL certificates:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to this directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/

# Set correct permissions
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```

## Option 2: Self-Signed Certificate (Development Only)

For development/testing, generate a self-signed certificate:

```bash
# Run the provided script
bash scripts/generate-ssl-cert.sh

# Or manually:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**⚠️ WARNING**: Self-signed certificates should NEVER be used in production!

## Automatic Renewal (Let's Encrypt)

Set up automatic renewal for Let's Encrypt certificates:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab (renew twice daily)
echo "0 0,12 * * * root certbot renew --quiet && docker-compose -f docker-compose.queue.yml restart nginx" | sudo tee -a /etc/crontab
```

## Permissions

```bash
# Ensure correct permissions
chmod 755 nginx/ssl
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```
