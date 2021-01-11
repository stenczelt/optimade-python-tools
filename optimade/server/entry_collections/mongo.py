from typing import Dict, Tuple, List, Any
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import MongoTransformer
from optimade.models import EntryResource
from optimade.server.config import CONFIG
from optimade.server.entry_collections import EntryCollection
from optimade.server.logger import LOGGER
from optimade.server.mappers import BaseResourceMapper


if CONFIG.database_backend.value == "mongodb":
    from pymongo import MongoClient

    client = MongoClient(CONFIG.mongo_uri)
    LOGGER.info("Using: Real MongoDB (pymongo)")

elif CONFIG.database_backend.value == "mongomock":
    from mongomock import MongoClient

    client = MongoClient()
    LOGGER.info("Using: Mock MongoDB (mongomock)")

if CONFIG.database_backend.value in ("mongomock", "mongodb"):
    CLIENT = MongoClient(CONFIG.mongo_uri)


class MongoCollection(EntryCollection):
    """Class for querying MongoDB collections (implemented by either pymongo or mongomock)
    containing serialized [`EntryResource`][optimade.models.entries.EntryResource]s objects.

    """

    def __init__(
        self,
        name: str,
        resource_cls: EntryResource,
        resource_mapper: BaseResourceMapper,
        database: str = CONFIG.mongo_database,
    ):
        """Initialize the MongoCollection for the given parameters.

        Parameters:
            name: The name of the collection.
            resource_cls: The type of entry resource that is stored by the collection.
            resource_mapper: A resource mapper object that handles aliases and
                format changes between deserialization and response.
            database: The name of the underlying MongoDB database to connect to.

        """
        super().__init__(
            resource_cls,
            resource_mapper,
            MongoTransformer(mapper=resource_mapper),
        )

        self.parser = LarkParser(version=(1, 0, 0), variant="default")
        self.collection = client[database][name]

        # check aliases do not clash with mongo operators
        self._check_aliases(self.resource_mapper.all_aliases())
        self._check_aliases(self.resource_mapper.all_length_aliases())

    def __len__(self) -> int:
        return self.collection.estimated_document_count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry: EntryResource) -> bool:
        raise NotImplementedError

    def count(self, **kwargs) -> int:
        """Returns the number of entries matching the query specified
        by the keyword arguments.

        Parameters:
            kwargs (dict): Query parameters as keyword arguments. The keys
                'filter', 'skip', 'limit', 'hint' and 'maxTimeMS' will be passed
                to the `pymongo.collection.Collection.count_documents` method.

        """
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return self.collection.count_documents(**kwargs)

    def insert(self, data: List[EntryResource]):
        self.collection.insert_many(data)

    def _run_db_query(
        self, criteria: Dict[str, Any], single_entry: bool = False
    ) -> Tuple[List[Dict[str, Any]], int, bool]:

        results = []
        for doc in self.collection.find(**criteria):
            if criteria.get("projection", {}).get("_id"):
                doc["_id"] = str(doc["_id"])
            results.append(doc)

        nresults_now = len(results)
        if not single_entry:
            criteria_nolimit = criteria.copy()
            criteria_nolimit.pop("limit", None)
            data_returned = self.count(**criteria_nolimit)
            more_data_available = nresults_now < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = nresults_now
            more_data_available = False
            if nresults_now > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {nresults_now} entries were found",
                )
            results = results[0] if results else None

        return results, data_returned, more_data_available

    def _check_aliases(self, aliases):
        """ Check that aliases do not clash with mongo keywords. """
        if any(
            alias[0].startswith("$") or alias[1].startswith("$") for alias in aliases
        ):
            raise RuntimeError(f"Cannot define an alias starting with a '$': {aliases}")
