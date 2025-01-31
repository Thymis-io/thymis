import argparse
import os

from http_network_relay.access_client import AccessClient

parser = argparse.ArgumentParser()
parser.add_argument(
    "controller_access_client_endpoint", help="The controller access client endpoint"
)
parser.add_argument("deployment_info_id", help="The deployment info id")
parser.add_argument(
    "--secret",
    help="The secret used to authenticate with the relay",
    default=os.getenv("HTTP_NETWORK_RELAY_SECRET", None),
)


def main():
    args = parser.parse_args()
    access_client = AccessClient(
        args.deployment_info_id,
        "localhost",
        22,
        "tcp",
        args.controller_access_client_endpoint,
        args.secret,
    )
    access_client.run()


if __name__ == "__main__":
    main()
