import uuid

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = {} # id -> doc

    async def insert_one(self, doc):
        _id = str(uuid.uuid4())
        doc["_id"] = _id
        self.data[_id] = doc
        return type('obj', (object,), {'inserted_id': _id})

    async def find_one(self, filter_dict):
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc.copy()
        return None

    async def find(self, filter_dict):
        results = []
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc.copy())
        
        class Cursor:
            def __init__(self, data): self.data = data
            async def to_list(self, length=None): return self.data
        return Cursor(results)

    async def update_one(self, filter_dict, update_dict):
        doc = await self.find_one(filter_dict)
        if doc:
            _id = doc["_id"]
            if "$set" in update_dict:
                self.data[_id].update(update_dict["$set"])
            return True
        return False

    async def count_documents(self, filter_dict):
        count = 0
        for doc in self.data.values():
            match = True
            for k, v in filter_dict.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match: count += 1
        return count

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
