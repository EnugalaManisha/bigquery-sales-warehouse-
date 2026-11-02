"""Upload orders.csv to Cloud Storage, load it into BigQuery staging, then build the star schema.

Prerequisites:
  pip install -r requirements.txt
  gcloud auth application-default login
  export GCP_PROJECT=your-project-id
  export GCS_BUCKET=your-bucket-name
  export BQ_DATASET=sales_dw   # optional, defaults to sales_dw

Usage: python load_to_bigquery.py --csv data/orders.csv
"""
import argparse
import os
from pathlib import Path

from google.cloud import bigquery, storage

SQL_DIR = Path(__file__).parent / "sql"


def render(sql: str, project: str, dataset: str) -> str:
    return sql.replace("${PROJECT}", project).replace("${DATASET}", dataset)


def run_script(client: bigquery.Client, path: Path, project: str, dataset: str) -> None:
    print(f"Running {path.name} ...")
    client.query(render(path.read_text(), project, dataset)).result()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/orders.csv")
    args = ap.parse_args()

    project = os.environ["GCP_PROJECT"]
    bucket_name = os.environ["GCS_BUCKET"]
    dataset = os.environ.get("BQ_DATASET", "sales_dw")

    bq = bigquery.Client(project=project)
    gcs = storage.Client(project=project)

    # 1) Create dataset and staging table
    run_script(bq, SQL_DIR / "01_staging.sql", project, dataset)

    # 2) Upload CSV to Cloud Storage
    blob_name = f"raw/{Path(args.csv).name}"
    gcs.bucket(bucket_name).blob(blob_name).upload_from_filename(args.csv)
    uri = f"gs://{bucket_name}/{blob_name}"
    print(f"Uploaded to {uri}")

    # 3) Load CSV from GCS into staging
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    table_id = f"{project}.{dataset}.stg_orders"
    bq.load_table_from_uri(uri, table_id, job_config=job_config).result()
    print(f"Loaded {bq.get_table(table_id).num_rows} rows into {table_id}")

    # 4) Build the star schema
    run_script(bq, SQL_DIR / "02_star_schema.sql", project, dataset)
    print("Star schema built. Run sql/03_analytics.sql in the BigQuery console.")


if __name__ == "__main__":
    main()
