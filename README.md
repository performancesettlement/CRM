# CRM

Custom Python/Django based CRM for Performance Settlement operations



# Setup

First, set up [Docker Compose](https://www.docker.com/products/docker-compose).  Instructions are [provided for Ubuntu](scripts/setup_ubuntu.sh) tested on 14.04 to 16.04.

Obtain the appropriate credentials for the Amazon S3 bucket and place them in the `.env` file as such:

```
AWS_ACCESS_KEY_ID=ASDFGHJKLASDFGHJKLAS
AWS_SECRET_ACCESS_KEY=ASDFGHJKL1234567890asdfghjkl1234567890as
AWS_DEFAULT_REGION=us-west-2
```

If deploying for production, run `scripts/setup_production.sh`.

Finally, run the following command:

```
docker-compose up -d --build
```

The service will be made available on port 80 of the container.  In production mode, the service will listen on port 443 with TLS on the host system.  Check `docker-compose.production.yml` for production-specific settings, such as the publicly resolvable DNS address where the service will listen.



# Development

It's convenient to use a combination of [Consul and Registrator](https://github.com/mgomezch/local_services) to make the service available through a comfortable local DNS address.  Clone that repository and run `docker-compose up -d` in its root; if you followed the Ubuntu setup instructions, it should bring up the service at <http://crm_web.service.consul.test/>.

To work on the code, simply edit files in your repository clone and repeat the `docker-compose up -d --build` command to bring up your changes.
