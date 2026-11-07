# billing-api

Invoice service behind Ledgerly. Python 3.12, standard library only.

    python3 -m billing.app          # serve on :8080
    python3 -m pytest -q            # unit checks

CI runs on every change (see the platform repo's `pipeline.yaml`); deploy with
`deploy run --env staging|production`.
