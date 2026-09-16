#!/usr/bin/env bash
#
# Container entrypoint: waits for backing services, then runs idempotent
# instance setup before execing the real command (normally uwsgi, see
# Dockerfile CMD).
#
# Every setup command is tolerant of "already exists"-style failures (|| true)
# and runs on every boot rather than being gated by a marker file. A marker
# file in the container's ephemeral instance path can't tell you whether the
# *backing services* were already set up — named volumes outlive container
# recreation and may already hold state from a prior run.
#
# Vocabulary loading and test data are intentionally NOT done here — that
# belongs in pytest session-scoped fixtures so state can be controlled and
# isolated per test run.
set -uo pipefail

wait_for() {
    local name="$1" host="$2" port="$3"
    echo "Waiting for ${name} (${host}:${port})..." >&2
    for _ in $(seq 1 60); do
        if (echo > "/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
            echo "${name} is up." >&2
            return 0
        fi
        sleep 2
    done
    echo "Timed out waiting for ${name} (${host}:${port})" >&2
    exit 1
}

wait_for db     "${INVENIO_DATABASE_HOST:-db}"   "${INVENIO_DATABASE_PORT:-5432}" || exit 1
wait_for search "${INVENIO_OPENSEARCH_HOST:-search}" "${INVENIO_OPENSEARCH_PORT:-9200}" || exit 1
wait_for mq     "${INVENIO_RABBIT_HOST:-mq}"     "${INVENIO_RABBIT_PORT:-5672}"  || exit 1
wait_for s3     "${INVENIO_S3_HOST:-s3}"         "${INVENIO_S3_PORT:-9000}"      || exit 1

echo "Running instance setup (idempotent, safe to repeat)..." >&2

invenio db init create || true
invenio files location create --default default-location s3://default || true
invenio index init || true

invenio roles create administration || true
invenio access allow administration-access role administration || true
invenio access allow administration-moderation role administration || true
invenio users create -a -c "${INVENIO_ADMIN_EMAIL:-admin@testing.local}" \
    --password "${INVENIO_ADMIN_PASSWORD:-changeme}" || true
invenio roles add "${INVENIO_ADMIN_EMAIL:-admin@testing.local}" administration || true

invenio rdm-records custom-fields init || true
invenio communities custom-fields init || true
invenio queues declare || true

echo "Instance setup pass complete." >&2

exec "$@"
