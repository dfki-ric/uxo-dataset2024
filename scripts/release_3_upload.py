import os
import requests
import click


@click.command()
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@click.option("--key", prompt="Access token")
@click.option("--bucket", prompt="Bucket URL")
def main(files, key, bucket):
    for file in files:
        filename = os.path.basename(file)
        print(f"Uploading {filename} - please be patient...")

        with open(file, "rb") as fp:
            r = requests.put(
                f"{bucket}/{filename}", data=fp, params={"access_token": key}
            )
            print(f"{r.status_code}:\n{r.json()}")


if __name__ == "__main__":
    main()
