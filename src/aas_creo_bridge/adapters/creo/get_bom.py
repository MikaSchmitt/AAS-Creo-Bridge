import creopyson

def get_creo_bom(client: creopyson.Client, target_model: str) -> set[str]:
    """Fetch all unique component names from the assembly."""
    try:
        bom_res = client.bom_get_paths(file_=target_model, paths=True})
        unique_files: set[str] = set()

        def extract_recursive(node) -> None:
            if isinstance(node, list):
                for item in node:
                    extract_recursive(item)
            elif isinstance(node, dict):
                if "file" in node:
                    unique_files.add(node["file"])
                if "children" in node:
                    extract_recursive(node["children"])

        extract_recursive(bom_res)
        return unique_files
    except Exception as e:
        print(f"Error fetching BOM from Creo: {e}")
        return set()
