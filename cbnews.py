import sys
import time
import os
import datetime
from typing import Iterable, Union, Dict
import urllib.request
import csv
import argparse
import logging
import collections.abc
import functools
import json
import dataclasses


def parse_args(args: Iterable[str]):
    """Parse arguments"""
    parser = argparse.ArgumentParser(
        description=(
            "A command line ulitity to get"
            "press refrerences from Crunchbase.\n"
            "For more details, see"
            " https://app.swaggerhub.com/apis-docs/"
            "Crunchbase/crunchbase-enterprise_api/1.0.3\n\n"
            "Examples:\n\n"
            "collect press references posted on dates after 2017-01-01 \n"
            "with siemens entity ID. \n\n"
            f"> python3 {__file__} -b 2017-01-01 siemens output.csv.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("entity", help="entity ID")
    parser.add_argument("output", help="Output CSV file")
    parser.add_argument("-a", "--after", help="after_id")
    parser.add_argument(
        "-b",
        "--bound",
        default=datetime.datetime.fromisoformat("1970-01-01"),
        type=datetime.datetime.fromisoformat,
        help=(
            "Collect news posted on the dates "
            "equal or greater than the specified date."
        ),
    )

    parser.add_argument(
        "-v", "--verbose", action="store_const", const=True, help="Be verbose"
    )

    options = parser.parse_args(args)
    options.crunchbase_api_key = os.environ["CRUNCHBASE_API_KEY"]

    return options


def configure_log(verbose: bool):
    """ """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)


@dataclasses.dataclass
class PressReference:
    """
    identifier looks like a title.
    """

    organization_name: str
    reference: Dict

    def __init__(self, organization_name: str, reference: Dict):
        """ """
        self.organization_name = organization_name
        self.reference = reference

    @property
    def author(self) -> Union[str, None]:
        """ """
        return self.reference.get("author")

    @property
    def identifier(self) -> str:
        """ """
        return self.reference["identifier"]["uuid"]

    @property
    def abstract(self) -> str:
        """ """
        return self.reference["identifier"]["value"]

    @property
    def url(self) -> str:
        """ """
        return self.reference["url"]["value"]

    @property
    def posted_on(self) -> str:
        """ """
        return self.reference["posted_on"]

    def is_posted_on_egt(self, iso_format_date: datetime.datetime):
        posted_on = datetime.datetime.fromisoformat(self.posted_on)
        return posted_on >= iso_format_date

    def as_dict(self):
        return {
            "organization": self.organization_name,
            "author": self.author,
            "identifier": self.identifier,
            "abstract": self.abstract,
            "url": self.url,
            "posted_on": self.posted_on,
        }

    @classmethod
    def fields(cls):
        """ """
        return [
            "organization",
            "author",
            "identifier",
            "abstract",
            "url",
            "posted_on",
        ]


class PressReferences(collections.abc.Sequence):
    """ """

    def __init__(self, references: dict):
        """ """
        self.references = references

    def __len__(self):
        """ """
        return len(self.press_references)

    def __getitem__(self, index) -> PressReference:
        """ """
        organization_name = self.references["properties"]["identifier"][
            "value"
        ]
        reference = self.press_references[index]
        return PressReference(organization_name, reference)

    @property
    def press_references(self):
        return self.references["cards"]["press_references"]


def retry(time, waitseconds):
    def retry_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            while count < time:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    count += 1
                    logging.getLogger(__name__).warning(
                        f"{func.__name__} raised {e}. "
                        "Retry the function after "
                        f"sleeping for {waitseconds} seconds."
                    )
                    time.sleep(waitseconds)
                    if time <= count:
                        raise e

        return wrapper

    return retry_decorator


@retry(time=3, waitseconds=3)
def collect_news(
    entity_id: str,
    crunchbase_api_key: str,
    after_id: Union[str, None] = None,
    url_base="https://api.crunchbase.com/api/v4",
) -> PressReferences:
    """ """
    url = (
        f"{url_base}/entities/organizations/{entity_id}/"
        "cards/press_references?order=posted_on%20desc"
    )
    url = f"{url}&after_id={after_id}" if after_id else url
    logging.getLogger(__name__).debug(f"Sending a request to {url}.")
    with urllib.request.urlopen(
        urllib.request.Request(
            url=url,
            headers={
                "accept": "application/json",
                "x-cb-user-key": crunchbase_api_key,
            },
        ),
    ) as response:
        body = json.loads(response.read())
        if response.getcode() / 100 == 2:
            return PressReferences(body)
        else:
            logger = logging.getLogger(__name__)
            logger.error(
                f"status code: {response.getcode()}, error message: {body}"
            )
            logger.error(f"status code: {response.getcode()}")
            raise RuntimeError(
                {
                    "message": "HTTP request failure.",
                    "entity_id": entity_id,
                    "after_id": after_id,
                }
            )


if __name__ == "__main__":
    options = parse_args(sys.argv[1:])
    configure_log(options.verbose)
    with open(options.output, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=PressReference.fields())
        writer.writeheader()
        after_id = options.after
        proceed = True
        while proceed:
            references = collect_news(
                options.entity,
                after_id=after_id,
                crunchbase_api_key=options.crunchbase_api_key,
            )
            if len(references) == 0:
                break
            else:
                for reference in references:
                    if reference.is_posted_on_egt(options.bound):
                        writer.writerow(reference.as_dict())
                        after_id = reference.identifier
                    else:
                        proceed = False
