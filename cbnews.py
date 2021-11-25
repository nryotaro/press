import sys
import os
from typing import Iterable, Union, Dict
import urllib.request
import argparse
import logging
import collections.abc
import json
import dataclasses


def parse_args(args: Iterable[str]):
    """Parse arguments"""
    parser = argparse.ArgumentParser(
        description="https://app.swaggerhub.com/apis-docs/Crunchbase/crunchbase-enterprise_api/1.0.3"
    )
    parser.add_argument("entity", help="entity Id")
    parser.add_argument("-v", "--verbose", help="Be verbose")

    return parser.parse_args(
        args,
        namespace=argparse.Namespace(
            crunchbase_api_key=os.environ["CRUNCHBASE_API_KEY"]
        ),
    )


def configure_log(verbose: bool):
    """ """
    logging.getLogger("cbnews").setLevel(logging.DEBUG if verbose else logging.INFO)


@dataclasses.dataclass
class PressReference:
    """
    identifier looks like title.
    """
    organization_name: str
    reference: Dict

    def __init__(self, organization_name: str, reference: Dict):
        """
        """
        self.organization_name = organization_name
        self.reference = reference
    
    @property
    def author(self) -> Union[str, None]:
        """
        """
        return self.reference.get('author')
    @property
    def identifier(self) -> str:
        """
        """
        return self.reference['identifier']['value']

    @property
    def url(self) -> str:
        """
        """
        return self.reference['url']['value']
    
    @property
    def posted_on(self) -> str:
        """
        """
        return self.reference['posted_on']


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
        organization_name = self.references["properties"]["identifier"]["value"]
        reference = self.press_references[index]
        return PressReference(organization_name, reference)
        

    @property
    def press_references(self):
        return self.references["cards"]["press_references"]



def collect_news(
    entity_id: str,
    crunchbase_api_key: str,
    after_id: Union[str, None] = None,
    url_base="https://api.crunchbase.com/api/v4",
) -> PressReferences:
    """ """
    url = f"{url_base}/entities/organizations/{entity_id}/cards/press_references?order=posted_on%20desc"
    with urllib.request.urlopen(
        urllib.request.Request(
            url=f"{url}/after_id={after_id}" if after_id else url,
            headers={"accept": "application/json", "x-cb-user-key": crunchbase_api_key},
        ),
    ) as response:
        if response.getcode() % 100 == 2:
            pass
        else:
            logging.error(
                f"status code: {response.getcode()}, error message: {json.loads(response.read())}"
            )
            logging.error(f"status code: {response.getcode()}")
            raise RuntimeError({"entity_id": entity_id, "after_id": after_id})


if __name__ == "__main__":
    options = parse_args(sys.argv[1:])
    configure_log(options.verbose)

    collect_news("siemens", crunchbase_api_key=options.crunchbase_api_key)