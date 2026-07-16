# CodeSwitch observability

The Django service emits structured logs, OpenTelemetry traces/metrics, and a
Prometheus-compatible metrics endpoint. Telemetry never intentionally includes
submitted code, prompts, cookies, JWTs, passwords, or API keys.

## Railway configuration

The existing PostgreSQL service provides the shared rate-limit cache. Set
`TRUSTED_PROXY_COUNT=1` only after confirming Railway is the sole trusted
reverse proxy. Configure:

```env
SERVICE_NAME=codeswitch-backend
DEPLOYMENT_ENVIRONMENT=production
LOG_FORMAT=json
LOG_LEVEL=INFO
METRICS_ENABLED=True
METRICS_BEARER_TOKEN=<random-long-secret>
OTEL_EXPORTER_OTLP_ENDPOINT=<Grafana Cloud OTLP endpoint>
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <Grafana Cloud token>
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.10
```

Do not place the metrics token or OTLP credentials in Vercel. Verify:

```bash
curl https://<backend>/health/live
curl https://<backend>/health/ready
curl -H "Authorization: Bearer <token>" https://<backend>/metrics
```

Import `observability/grafana/codeswitch-overview.json` into Grafana and choose
the Grafana Cloud Prometheus data source. OTLP logs and traces use the same
service name, allowing Explore to correlate them by `trace_id`.

## Suggested alerts

- Readiness probe fails for 2 minutes.
- 5xx responses exceed 5% for 5 minutes.
- p95 HTTP latency exceeds 2 seconds for 10 minutes.
- Rate-limit rejections increase sharply by scope.
- AI or Wandbox dependency errors exceed 10% for 10 minutes.
- No `codeswitch_http_requests_total` samples arrive for 10 minutes during expected traffic.

Run `python manage.py prune_conversion_history --dry-run` before scheduling the
retention command. Railway cron may run it daily without `--dry-run`.
