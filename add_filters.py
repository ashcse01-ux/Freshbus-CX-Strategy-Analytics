import re

with open('backend/routers/helpdesk.py', 'r', encoding='utf-8') as f:
    py_code = f.read()

new_endpoint = """
@router.get("/filters")
async def get_filters():
    try:
        conn = get_db_connection()
        
        def get_distinct(table, column):
            cursor = conn.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
            return [row[0] for row in cursor.fetchall()]

        filters = {
            "lob": get_distinct("raw_tickets", "lob"),
            "status": get_distinct("raw_tickets", "st"),
            "type": get_distinct("raw_tickets", "typ"),
            "group": get_distinct("raw_tickets", "grp"),
            "priority": get_distinct("raw_tickets", "pri"),
            "agent": get_distinct("raw_tickets", "ag"),
            "source": get_distinct("raw_tickets", "src"),
            "hda_source": get_distinct("raw_calls", "camp") # HD adoption source
        }
        
        conn.close()
        return {"status": "success", "data": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

# Insert before @router.post("/aggregate")
py_code = py_code.replace('@router.post("/aggregate")', new_endpoint + '\n@router.post("/aggregate")')

with open('backend/routers/helpdesk.py', 'w', encoding='utf-8') as f:
    f.write(py_code)
