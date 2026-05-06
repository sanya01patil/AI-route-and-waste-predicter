import uuid

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {} # _id -> doc

    async def insert_one(self, doc):
        _id = str(uuid.uuid4())
        doc["_id"] = _id
        # Store a COPY so caller mutations don't corrupt stored data
        self.data[_id] = dict(doc)
        return type('obj', (object,), {'inserted_id': _id})

    def _matches(self, doc, filter_dict):
        """Supports basic MongoDB operators: $ne, $gt, $lt, $gte, $lte, $in"""
        for k, v in filter_dict.items():
            if isinstance(v, dict):
                field_val = doc.get(k)
                for op, op_val in v.items():
                    if op == "$ne" and field_val == op_val:
                        return False
                    elif op == "$gt" and not (field_val is not None and field_val > op_val):
                        return False
                    elif op == "$lt" and not (field_val is not None and field_val < op_val):
                        return False
                    elif op == "$gte" and not (field_val is not None and field_val >= op_val):
                        return False
                    elif op == "$lte" and not (field_val is not None and field_val <= op_val):
                        return False
                    elif op == "$in" and field_val not in op_val:
                        return False
            else:
                if doc.get(k) != v:
                    return False
        return True

    async def find_one(self, filter_dict):
        for doc in self.data.values():
            if self._matches(doc, filter_dict):
                return doc.copy()
        return None

    async def find(self, filter_dict):
        results = [doc.copy() for doc in self.data.values() if self._matches(doc, filter_dict)]

        class Cursor:
            def __init__(self, data): self.data = data
            async def to_list(self, length=None): return self.data
        return Cursor(results)

    async def update_one(self, filter_dict, update_dict):
        for _id, doc in self.data.items():
            if self._matches(doc, filter_dict):
                if "$set" in update_dict:
                    self.data[_id].update(update_dict["$set"])
                return True
        return False

    async def count_documents(self, filter_dict):
        return sum(1 for doc in self.data.values() if self._matches(doc, filter_dict))

    async def create_index(self, key, unique=False):
        pass # Mock

class MockRedis:
    def __init__(self):
        self.data = {}
    async def get(self, key): return self.data.get(key)
    async def set(self, key, val, ex=None): self.data[key] = val
    async def delete(self, key): self.data.pop(key, None)
    @classmethod
    def from_url(cls, url, **kwargs): return cls()
