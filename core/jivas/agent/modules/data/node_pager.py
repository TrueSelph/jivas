"""NodePager class for paginating node collections in Jivas."""

from jac_cloud.jaseci.datasources.collection import Collection

"""
# Initialize pager
pager = Pager(NodeAnchor.Collection, page_size=10, current_page=2)

# Get a page of results
doc_entries = pager.get_page({"name": "DocFileEntry"})

# get all info as a dict
pagination_info = pager.to_dict()

"""


class NodePager:
    """A class to handle pagination of nodes in a collection."""

    def __init__(
        self,
        collection: Collection,
        page_size: int = 10,
        current_page: int = 1,
    ) -> None:
        """Initialize the NodePager with a collection, optional root, page size, and current page."""
        self.collection = collection
        self.page_size = page_size
        self.current_page = current_page
        self.total_items = 0
        self.total_pages = 1
        self.has_previous = False
        self.has_next = False

    def get_page(self, query_filter: dict | None = None) -> list:
        """Retrieve a paginated list of nodes based on the query filter."""

        if query_filter is None:
            query_filter = {}

        # Get total count of items matching the filter
        self.total_items = self.collection.count(query_filter)

        # Calculate total pages
        self.total_pages = max(
            1, (self.total_items + self.page_size - 1) // self.page_size
        )

        # Ensure current_page is within bounds
        self.current_page = max(1, min(self.current_page, self.total_pages))

        # Calculate pagination flags
        self.has_previous = self.current_page > 1
        self.has_next = self.current_page < self.total_pages

        # Calculate skip value
        skip = (self.current_page - 1) * self.page_size

        # Execute the query
        items = self.collection.find(
            query_filter,
            skip=skip,
            limit=self.page_size,
        )

        if items:
            nodes = [n.archetype for n in items]
            return nodes

        return []

    @property
    def previous_page(self) -> int | None:
        """Return the previous page number if available, otherwise None."""
        return self.current_page - 1 if self.has_previous else None

    @property
    def next_page(self) -> int | None:
        """Return the next page number if available, otherwise None."""
        return self.current_page + 1 if self.has_next else None

    def to_dict(self) -> dict:
        """Return a dictionary representation of the pagination state."""
        return {
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "has_previous": self.has_previous,
            "has_next": self.has_next,
            "page_size": self.page_size,
        }
