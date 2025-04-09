## 2.0.0-alpha.24
- Updated data param in interact walker to accept a list of data items; added serialization to dump_yaml function

## 2.0.0-alpha.25
- Updated interact walker's data param to accept a list of dict items each with the keys "label", "meta", "content"
- Fixed false positive on add_texts execution when ingestion fails in base vector_store_action