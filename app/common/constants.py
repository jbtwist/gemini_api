import uuid

# This is a storage simulation. Is going to keep track in memory of the uploaded files for this API.
# Normally, this would be a combination of RDB + Cache with a proper strategy, but I will keep it simple.
PROJECT_FILE_STORE = {}

# Each user has an unique ID which would be used to identify their file store.
# However, we don't have authentication in this assessment, so we will simulate with a single user.
user_uuid = str(uuid.uuid4())


