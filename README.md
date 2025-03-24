# ExaMon Docker Image

## Build

```bash
docker build -t examonhpc/examon:0.3.0 .
```

## Run

```bash
docker run -d --name examon_0 \
--log-opt max-size=50m \
--restart=always \
--net=bridge \
-p 1883:1883 \
-p 9001:9001 \
-e EX_KAIROSDB_HOST=127.0.0.1 \
examonhpc/examon:0.3.0
```

