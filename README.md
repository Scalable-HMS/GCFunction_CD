# CD Function

```bash
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
```

Push to GCF

```bash
gcloud functions deploy deploy_to_k8s --runtime python39 --trigger-topic gcr --vpc-connector jumboxconnector
```

Check logs

```bash
gcloud functions logs read --limit 20
```
