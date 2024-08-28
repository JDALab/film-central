__all__ = ()

# A hardcoded dictionary of common search terms that when 
# entered into bflix won't return any results or the results you are expecting.
# 
# This is my attempt to help fix that.
QUERIES_CORRECTIONS = {
    "Spider-Man": ("spiderman",)
}

def optimize_query(query: str) -> str:

    for correct_query, wrong_queries in QUERIES_CORRECTIONS.items():

        if query.lower() in wrong_queries:
            return correct_query

    return query